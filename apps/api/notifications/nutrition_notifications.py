from datetime import timedelta
from django.utils import timezone
from apps.api.notification_service_v2 import NotificationService
from apps.api.models import DailyNutrition, FoodAnalysis, UserProfile
import logging

logger = logging.getLogger(__name__)


class NutritionNotificationService:
    """영양 관리 관련 알림 서비스"""
    
    @staticmethod
    def send_meal_reminder(user, meal_type):
        """식사 기록 리마인더"""
        meal_names = {
            'breakfast': ('아침', 'Breakfast', 'Desayuno'),
            'lunch': ('점심', 'Lunch', 'Almuerzo'),
            'dinner': ('저녁', 'Dinner', 'Cena'),
            'snack': ('간식', 'Snack', 'Merienda'),
        }
        
        meal_ko, meal_en, meal_es = meal_names.get(
            meal_type,
            ('식사', 'Meal', 'Comida')
        )
        
        NotificationService.create_notification(
            user=user,
            notification_type='reminder',
            title_ko=f'{meal_ko} 시간입니다',
            title_en=f'Time for {meal_en}',
            title_es=f'Hora de {meal_es}',
            message_ko=f'{meal_ko} 식사를 기록해주세요. 균형잡힌 영양 섭취가 중요해요!',
            message_en=f'Don\'t forget to log your {meal_en.lower()}. Balanced nutrition is important!',
            message_es=f'No olvides registrar tu {meal_es.lower()}. ¡La nutrición equilibrada es importante!',
            metadata={
                'icon': 'restaurant',
                'meal_type': meal_type,
                'reminder_type': 'meal'
            },
            action_url='/nutrition/log'
        )
    
    @staticmethod
    def send_calorie_goal_notification(user, current_calories, target_calories):
        """칼로리 목표 관련 알림"""
        percentage = (current_calories / target_calories) * 100
        
        if percentage >= 100:
            # 목표 달성
            NotificationService.create_notification(
                user=user,
                notification_type='achievement',
                title_ko='일일 칼로리 목표 달성!',
                title_en='Daily Calorie Goal Achieved!',
                title_es='¡Meta de Calorías Diarias Lograda!',
                message_ko=f'오늘의 칼로리 목표 {target_calories}kcal를 달성했습니다!',
                message_en=f'You\'ve reached your daily calorie goal of {target_calories}kcal!',
                message_es=f'¡Has alcanzado tu meta diaria de {target_calories}kcal!',
                metadata={
                    'icon': 'achievement',
                    'current_calories': current_calories,
                    'target_calories': target_calories,
                    'achievement_type': 'calorie_goal'
                },
                action_url='/nutrition/dashboard'
            )
        elif percentage >= 120:
            # 초과 경고
            NotificationService.create_notification(
                user=user,
                notification_type='warning',
                title_ko='칼로리 초과 주의',
                title_en='Calorie Limit Exceeded',
                title_es='Límite de Calorías Excedido',
                message_ko=f'오늘 섭취 칼로리가 목표치를 {int(percentage - 100)}% 초과했습니다.',
                message_en=f'Today\'s calorie intake exceeded your goal by {int(percentage - 100)}%.',
                message_es=f'La ingesta de calorías de hoy excedió tu meta en {int(percentage - 100)}%.',
                metadata={
                    'icon': 'warning',
                    'current_calories': current_calories,
                    'target_calories': target_calories,
                    'excess_percentage': int(percentage - 100)
                },
                action_url='/nutrition/analysis'
            )
    
    @staticmethod
    def send_nutrient_imbalance_alert(user, nutrient_analysis):
        """영양소 불균형 경고 알림"""
        imbalanced_nutrients = []
        
        # 영양소 분석
        for nutrient, data in nutrient_analysis.items():
            if data['percentage'] < 80:
                imbalanced_nutrients.append({
                    'name': nutrient,
                    'percentage': data['percentage'],
                    'status': 'low'
                })
            elif data['percentage'] > 120:
                imbalanced_nutrients.append({
                    'name': nutrient,
                    'percentage': data['percentage'],
                    'status': 'high'
                })
        
        if imbalanced_nutrients:
            nutrient_names = {
                'protein': ('단백질', 'Protein', 'Proteína'),
                'carbs': ('탄수화물', 'Carbohydrates', 'Carbohidratos'),
                'fat': ('지방', 'Fat', 'Grasa'),
                'fiber': ('식이섬유', 'Fiber', 'Fibra'),
                'vitamins': ('비타민', 'Vitamins', 'Vitaminas'),
            }
            
            # 가장 심각한 불균형 영양소
            most_imbalanced = max(imbalanced_nutrients, 
                                 key=lambda x: abs(x['percentage'] - 100))
            
            nutrient_ko, nutrient_en, nutrient_es = nutrient_names.get(
                most_imbalanced['name'],
                (most_imbalanced['name'], most_imbalanced['name'], most_imbalanced['name'])
            )
            
            if most_imbalanced['status'] == 'low':
                NotificationService.create_notification(
                    user=user,
                    notification_type='health',
                    title_ko='영양소 부족 알림',
                    title_en='Nutrient Deficiency Alert',
                    title_es='Alerta de Deficiencia Nutricional',
                    message_ko=f'{nutrient_ko} 섭취가 부족합니다. 균형잡힌 식단을 위해 보충이 필요해요.',
                    message_en=f'Your {nutrient_en} intake is low. Consider adding more to your diet.',
                    message_es=f'Tu ingesta de {nutrient_es} es baja. Considera agregar más a tu dieta.',
                    metadata={
                        'icon': 'nutrition',
                        'nutrient': most_imbalanced['name'],
                        'percentage': most_imbalanced['percentage'],
                        'status': 'low'
                    },
                    action_url='/nutrition/recommendations'
                )
    
    @staticmethod
    def send_water_intake_reminder(user, current_intake, daily_goal):
        """수분 섭취 리마인더"""
        percentage = (current_intake / daily_goal) * 100
        
        if percentage < 50 and timezone.now().hour >= 14:  # 오후 2시 이후 50% 미만
            NotificationService.create_notification(
                user=user,
                notification_type='reminder',
                title_ko='물 마실 시간!',
                title_en='Time to Hydrate!',
                title_es='¡Hora de Hidratarse!',
                message_ko=f'오늘 목표의 {int(percentage)}%만 마셨어요. 물 한 잔 어때요? 💧',
                message_en=f'You\'ve only reached {int(percentage)}% of your daily water goal. Time for a glass! 💧',
                message_es=f'Solo has alcanzado el {int(percentage)}% de tu meta diaria de agua. ¡Hora de un vaso! 💧',
                metadata={
                    'icon': 'water',
                    'current_intake': current_intake,
                    'daily_goal': daily_goal,
                    'percentage': int(percentage)
                },
                action_url='/nutrition/water'
            )
    
    @staticmethod
    def send_ai_nutrition_analysis_complete(user, analysis_result):
        """AI 영양 분석 완료 알림"""
        total_calories = analysis_result.get('total_calories', 0)
        meal_name = analysis_result.get('meal_name', '음식')
        
        NotificationService.create_notification(
            user=user,
            notification_type='ai',
            title_ko='AI 영양 분석 완료',
            title_en='AI Nutrition Analysis Complete',
            title_es='Análisis Nutricional AI Completo',
            message_ko=f'{meal_name}의 분석이 완료되었습니다. 약 {total_calories}kcal로 추정됩니다.',
            message_en=f'Analysis of {meal_name} is complete. Estimated at {total_calories}kcal.',
            message_es=f'El análisis de {meal_name} está completo. Estimado en {total_calories}kcal.',
            metadata={
                'icon': 'ai_analysis',
                'meal_name': meal_name,
                'total_calories': total_calories,
                'analysis_id': analysis_result.get('id')
            },
            action_url=f'/nutrition/analysis/{analysis_result.get("id")}'
        )
    
    @staticmethod
    def send_meal_plan_suggestion(user, meal_plan):
        """식단 계획 제안 알림"""
        NotificationService.create_notification(
            user=user,
            notification_type='suggestion',
            title_ko='오늘의 추천 식단',
            title_en='Today\'s Meal Plan',
            title_es='Plan de Comidas de Hoy',
            message_ko='AI가 분석한 맞춤 식단을 확인해보세요!',
            message_en='Check out your AI-powered personalized meal plan!',
            message_es='¡Revisa tu plan de comidas personalizado con IA!',
            metadata={
                'icon': 'meal_plan',
                'plan_id': meal_plan.get('id'),
                'total_calories': meal_plan.get('total_calories'),
                'meal_count': meal_plan.get('meal_count')
            },
            action_url='/nutrition/meal-plans'
        )
    
    @staticmethod
    def send_nutrition_streak_notification(user, streak_days):
        """영양 기록 연속 일수 알림"""
        milestones = {
            3: ('3일 연속 영양 기록!', '3 Day Nutrition Tracking!', '¡3 días de registro nutricional!'),
            7: ('일주일 연속 영양 기록!', '1 Week Nutrition Tracking!', '¡1 semana de registro nutricional!'),
            30: ('한 달 연속 영양 기록!', '1 Month Nutrition Tracking!', '¡1 mes de registro nutricional!'),
        }
        
        if streak_days in milestones:
            title_ko, title_en, title_es = milestones[streak_days]
            
            NotificationService.create_notification(
                user=user,
                notification_type='achievement',
                title_ko=title_ko,
                title_en=title_en,
                title_es=title_es,
                message_ko=f'꾸준한 영양 관리가 건강의 시작입니다! {streak_days}일 연속 달성!',
                message_en=f'Consistent nutrition tracking is key to health! {streak_days} days achieved!',
                message_es=f'¡El seguimiento nutricional constante es clave para la salud! ¡{streak_days} días logrados!',
                metadata={
                    'icon': 'achievement',
                    'streak_days': streak_days,
                    'badge_type': 'nutrition_streak'
                },
                action_url='/achievements'
            )
