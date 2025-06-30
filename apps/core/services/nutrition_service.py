"""
식단 관련 서비스 레이어
성능 최적화를 위한 비즈니스 로직 캡슐화
"""
from django.db import transaction
from django.db.models import Q, Count, Avg, Sum, F
from django.utils import timezone
from datetime import timedelta, date
from typing import Dict, List, Optional, Tuple
import json
from ..models import DietLog, User, UserProfile

class NutritionService:
    """식단 관련 서비스"""
    
    # 한국 음식 영양 정보 데이터베이스 (샘플)
    FOOD_DATABASE = {
        '밥': {'calories': 130, 'protein': 2.7, 'carbs': 28.2, 'fat': 0.3, 'unit': '100g'},
        '김치': {'calories': 15, 'protein': 1.1, 'carbs': 2.4, 'fat': 0.5, 'unit': '100g'},
        '된장찌개': {'calories': 60, 'protein': 4.5, 'carbs': 5.2, 'fat': 2.8, 'unit': '100g'},
        '삼겹살': {'calories': 331, 'protein': 17.0, 'carbs': 0, 'fat': 29.0, 'unit': '100g'},
        '계란': {'calories': 155, 'protein': 13.0, 'carbs': 1.1, 'fat': 11.0, 'unit': '100g'},
        '닭가슴살': {'calories': 165, 'protein': 31.0, 'carbs': 0, 'fat': 3.6, 'unit': '100g'},
        '샐러드': {'calories': 20, 'protein': 1.5, 'carbs': 3.5, 'fat': 0.2, 'unit': '100g'},
        '우유': {'calories': 67, 'protein': 3.4, 'carbs': 4.8, 'fat': 3.7, 'unit': '100ml'},
        '사과': {'calories': 52, 'protein': 0.3, 'carbs': 14.0, 'fat': 0.2, 'unit': '100g'},
        '바나나': {'calories': 89, 'protein': 1.1, 'carbs': 23.0, 'fat': 0.3, 'unit': '100g'},
    }
    
    @staticmethod
    def get_user_diet_logs(
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[DietLog]:
        """사용자 식단 기록 조회 (최적화)"""
        queryset = DietLog.objects.filter(user=user).select_related('user')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date', 'meal_type')
    
    @staticmethod
    @transaction.atomic
    def create_diet_log(user: User, diet_data: Dict) -> DietLog:
        """식단 기록 생성"""
        # 음식 항목에서 영양 정보 계산
        food_items = diet_data.get('food_items', [])
        nutrition_info = NutritionService._calculate_nutrition(food_items)
        
        # 영양 정보 추가
        diet_data.update(nutrition_info)
        
        # 중복 체크 (같은 날짜, 같은 meal_type)
        existing = DietLog.objects.filter(
            user=user,
            date=diet_data['date'],
            meal_type=diet_data['meal_type']
        ).first()
        
        if existing:
            # 기존 기록 업데이트
            for key, value in diet_data.items():
                setattr(existing, key, value)
            existing.save()
            return existing
        else:
            # 새 기록 생성
            return DietLog.objects.create(user=user, **diet_data)
    
    @staticmethod
    def _calculate_nutrition(food_items: List[Dict]) -> Dict:
        """음식 목록에서 영양 정보 계산"""
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        total_fiber = 0
        
        for item in food_items:
            food_name = item.get('name', '')
            quantity = item.get('quantity', 1)
            
            # 데이터베이스에서 영양 정보 조회
            if food_name in NutritionService.FOOD_DATABASE:
                nutrition = NutritionService.FOOD_DATABASE[food_name]
                # 양에 따른 계산 (기본 단위는 100g/100ml)
                multiplier = quantity / 100
                
                total_calories += nutrition['calories'] * multiplier
                total_protein += nutrition['protein'] * multiplier
                total_carbs += nutrition['carbs'] * multiplier
                total_fat += nutrition['fat'] * multiplier
                # fiber는 데이터베이스에 없으면 탄수화물의 10%로 추정
                total_fiber += nutrition.get('fiber', nutrition['carbs'] * 0.1) * multiplier
        
        return {
            'total_calories': int(total_calories),
            'protein': round(total_protein, 1),
            'carbohydrates': round(total_carbs, 1),
            'fat': round(total_fat, 1),
            'fiber': round(total_fiber, 1)
        }
    
    @staticmethod
    def get_nutrition_summary(user: User, period_days: int = 7) -> Dict:
        """영양 섭취 요약 통계"""
        start_date = timezone.now().date() - timedelta(days=period_days)
        
        # 기본 통계
        basic_stats = DietLog.objects.filter(
            user=user,
            date__gte=start_date
        ).aggregate(
            total_meals=Count('id'),
            avg_calories=Avg('total_calories'),
            total_calories=Sum('total_calories'),
            avg_protein=Avg('protein'),
            avg_carbs=Avg('carbohydrates'),
            avg_fat=Avg('fat')
        )
        
        # 일별 칼로리 추이
        daily_calories = DietLog.objects.filter(
            user=user,
            date__gte=start_date
        ).values('date').annotate(
            calories=Sum('total_calories'),
            meals=Count('id')
        ).order_by('date')
        
        # 식사별 분포
        meal_distribution = DietLog.objects.filter(
            user=user,
            date__gte=start_date
        ).values('meal_type').annotate(
            count=Count('id'),
            avg_calories=Avg('total_calories')
        )
        
        # 영양소 비율 계산
        total_macros = (
            (basic_stats.get('avg_protein', 0) or 0) +
            (basic_stats.get('avg_carbs', 0) or 0) +
            (basic_stats.get('avg_fat', 0) or 0)
        )
        
        macro_ratio = {
            'protein': round((basic_stats.get('avg_protein', 0) or 0) / total_macros * 100, 1) if total_macros > 0 else 0,
            'carbs': round((basic_stats.get('avg_carbs', 0) or 0) / total_macros * 100, 1) if total_macros > 0 else 0,
            'fat': round((basic_stats.get('avg_fat', 0) or 0) / total_macros * 100, 1) if total_macros > 0 else 0
        }
        
        return {
            'basic_stats': basic_stats,
            'daily_calories': list(daily_calories),
            'meal_distribution': list(meal_distribution),
            'macro_ratio': macro_ratio,
            'period_days': period_days
        }
    
    @staticmethod
    def get_nutrition_recommendations(user: User) -> Dict:
        """사용자 맞춤 영양 권장량"""
        profile = user.profile if hasattr(user, 'profile') else None
        
        if not profile:
            # 기본값 반환
            return {
                'daily_calories': 2000,
                'protein': 50,
                'carbs': 300,
                'fat': 65,
                'fiber': 25,
                'water': 2.0
            }
        
        # 기초대사율(BMR) 계산 - Mifflin-St Jeor 공식
        if profile.gender == 'M':
            bmr = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age + 5
        else:
            bmr = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age - 161
        
        # 활동 계수 적용
        activity_multipliers = {
            'beginner': 1.2,      # 운동 거의 안함
            'intermediate': 1.375, # 가벼운 운동 (주 1-3회)
            'advanced': 1.55,     # 중간 강도 운동 (주 3-5회)
            'expert': 1.725       # 강한 운동 (주 6-7회)
        }
        
        activity_multiplier = activity_multipliers.get(profile.exercise_experience, 1.375)
        
        # 목표에 따른 칼로리 조정
        goal_adjustments = {
            'weight_loss': -500,      # 주당 0.5kg 감량
            'muscle_gain': 300,       # 근육 증가를 위한 잉여 칼로리
            'health_improvement': 0,  # 유지
            'endurance': 200,         # 지구력 향상을 위한 추가 칼로리
            'flexibility': 0,         # 유지
            'stress_relief': 0,       # 유지
            'custom': 0              # 유지
        }
        
        goal_adjustment = goal_adjustments.get(profile.goal, 0)
        
        # 일일 칼로리 권장량
        daily_calories = int(bmr * activity_multiplier + goal_adjustment)
        
        # 영양소 분배 (목표별)
        if profile.goal == 'muscle_gain':
            protein_ratio = 0.30  # 30%
            carbs_ratio = 0.45    # 45%
            fat_ratio = 0.25      # 25%
        elif profile.goal == 'weight_loss':
            protein_ratio = 0.35  # 35% (근육 보존)
            carbs_ratio = 0.35    # 35%
            fat_ratio = 0.30      # 30%
        else:
            protein_ratio = 0.25  # 25%
            carbs_ratio = 0.50    # 50%
            fat_ratio = 0.25      # 25%
        
        # 영양소별 권장량 계산
        protein_grams = int((daily_calories * protein_ratio) / 4)  # 1g = 4kcal
        carbs_grams = int((daily_calories * carbs_ratio) / 4)     # 1g = 4kcal
        fat_grams = int((daily_calories * fat_ratio) / 9)         # 1g = 9kcal
        
        # 수분 권장량 (체중 1kg당 30-35ml)
        water_liters = round(profile.weight * 0.033, 1)
        
        return {
            'daily_calories': daily_calories,
            'protein': protein_grams,
            'carbs': carbs_grams,
            'fat': fat_grams,
            'fiber': 25 if profile.gender == 'F' else 30,
            'water': water_liters,
            'notes': {
                'bmr': int(bmr),
                'activity_level': profile.exercise_experience,
                'goal': profile.goal
            }
        }
    
    @staticmethod
    def analyze_nutrition_balance(user: User, days: int = 7) -> Dict:
        """영양 균형 분석"""
        recommendations = NutritionService.get_nutrition_recommendations(user)
        summary = NutritionService.get_nutrition_summary(user, days)
        
        # 권장량 대비 섭취량 비교
        avg_calories = summary['basic_stats'].get('avg_calories', 0) or 0
        avg_protein = summary['basic_stats'].get('avg_protein', 0) or 0
        avg_carbs = summary['basic_stats'].get('avg_carbs', 0) or 0
        avg_fat = summary['basic_stats'].get('avg_fat', 0) or 0
        
        analysis = {
            'calories': {
                'recommended': recommendations['daily_calories'],
                'actual': int(avg_calories),
                'percentage': round((avg_calories / recommendations['daily_calories']) * 100, 1) if recommendations['daily_calories'] > 0 else 0,
                'status': 'adequate' if 0.9 <= (avg_calories / recommendations['daily_calories']) <= 1.1 else 'needs_adjustment'
            },
            'protein': {
                'recommended': recommendations['protein'],
                'actual': int(avg_protein),
                'percentage': round((avg_protein / recommendations['protein']) * 100, 1) if recommendations['protein'] > 0 else 0,
                'status': 'adequate' if avg_protein >= recommendations['protein'] * 0.8 else 'insufficient'
            },
            'carbs': {
                'recommended': recommendations['carbs'],
                'actual': int(avg_carbs),
                'percentage': round((avg_carbs / recommendations['carbs']) * 100, 1) if recommendations['carbs'] > 0 else 0,
                'status': 'adequate' if 0.8 <= (avg_carbs / recommendations['carbs']) <= 1.2 else 'needs_adjustment'
            },
            'fat': {
                'recommended': recommendations['fat'],
                'actual': int(avg_fat),
                'percentage': round((avg_fat / recommendations['fat']) * 100, 1) if recommendations['fat'] > 0 else 0,
                'status': 'adequate' if 0.8 <= (avg_fat / recommendations['fat']) <= 1.2 else 'needs_adjustment'
            }
        }
        
        # 개선 제안
        suggestions = []
        
        if analysis['calories']['status'] != 'adequate':
            if avg_calories < recommendations['daily_calories'] * 0.9:
                suggestions.append('일일 칼로리 섭취량이 부족합니다. 건강한 간식을 추가해보세요.')
            else:
                suggestions.append('일일 칼로리 섭취량이 많습니다. portion 크기를 조절해보세요.')
        
        if analysis['protein']['status'] == 'insufficient':
            suggestions.append('단백질 섭취가 부족합니다. 닭가슴살, 생선, 콩류를 추가해보세요.')
        
        if avg_calories > 0:
            # 영양소 비율 체크
            carb_ratio = (avg_carbs * 4) / avg_calories
            if carb_ratio > 0.65:
                suggestions.append('탄수화물 비중이 높습니다. 단백질과 건강한 지방의 비중을 늘려보세요.')
        
        return {
            'analysis': analysis,
            'suggestions': suggestions,
            'period_days': days
        }
