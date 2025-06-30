"""
사용자 관련 서비스 레이어
성능 최적화를 위한 비즈니스 로직 캡슐화
"""
from django.db import transaction
from django.db.models import Prefetch, Count, Avg, Sum, Q, F
from django.utils import timezone
from datetime import timedelta
from typing import Dict, List, Optional, Tuple
from ..models import User, UserProfile, WorkoutLog, DietLog, ChatSession

class UserService:
    """사용자 관련 서비스"""
    
    @staticmethod
    def get_user_with_profile(user_id: int) -> Optional[User]:
        """프로필 정보를 포함한 사용자 조회 (최적화)"""
        return User.objects.select_related('profile').filter(id=user_id).first()
    
    @staticmethod
    def get_user_statistics(user: User, days: int = 30) -> Dict:
        """사용자 통계 정보 조회 (최적화된 쿼리)"""
        start_date = timezone.now().date() - timedelta(days=days)
        
        # 운동 통계
        workout_stats = WorkoutLog.objects.filter(
            user=user,
            date__gte=start_date
        ).aggregate(
            total_workouts=Count('id'),
            total_duration=Sum('duration'),
            total_calories=Sum('calories_burned'),
            avg_duration=Avg('duration'),
            total_distance=Sum('distance'),
            total_steps=Sum('steps')
        )
        
        # 식단 통계
        diet_stats = DietLog.objects.filter(
            user=user,
            date__gte=start_date
        ).aggregate(
            total_meals=Count('id'),
            total_calories=Sum('total_calories'),
            avg_calories=Avg('total_calories'),
            total_protein=Sum('protein'),
            total_carbs=Sum('carbohydrates'),
            total_fat=Sum('fat')
        )
        
        # 주간 운동 횟수
        week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
        weekly_workouts = WorkoutLog.objects.filter(
            user=user,
            date__gte=week_start
        ).count()
        
        # 월간 목표 달성률 계산
        profile = user.profile
        monthly_stats = {
            'workout_goal_progress': 0,
            'distance_goal_progress': 0,
            'calories_goal_progress': 0,
            'steps_goal_progress': 0
        }
        
        if hasattr(user, 'profile'):
            month_start = timezone.now().date().replace(day=1)
            monthly_workouts = WorkoutLog.objects.filter(
                user=user,
                date__gte=month_start
            ).aggregate(
                count=Count('id'),
                total_distance=Sum('distance'),
                total_calories=Sum('calories_burned')
            )
            
            # 일일 걸음 수 평균
            daily_steps = WorkoutLog.objects.filter(
                user=user,
                date=timezone.now().date()
            ).aggregate(total=Sum('steps'))['total'] or 0
            
            # 목표 달성률 계산
            if profile.weekly_workout_goal > 0:
                monthly_stats['workout_goal_progress'] = min(
                    (weekly_workouts / profile.weekly_workout_goal) * 100, 100
                )
            
            if profile.monthly_distance_goal > 0:
                monthly_stats['distance_goal_progress'] = min(
                    ((monthly_workouts['total_distance'] or 0) / profile.monthly_distance_goal) * 100, 100
                )
            
            if profile.monthly_calories_goal > 0:
                monthly_stats['calories_goal_progress'] = min(
                    ((monthly_workouts['total_calories'] or 0) / profile.monthly_calories_goal) * 100, 100
                )
            
            if profile.daily_steps_goal > 0:
                monthly_stats['steps_goal_progress'] = min(
                    (daily_steps / profile.daily_steps_goal) * 100, 100
                )
        
        return {
            'workout_stats': workout_stats,
            'diet_stats': diet_stats,
            'weekly_workouts': weekly_workouts,
            'monthly_stats': monthly_stats,
            'period_days': days
        }
    
    @staticmethod
    @transaction.atomic
    def update_user_preferences(user: User, preferences: Dict) -> UserProfile:
        """사용자 선호도 업데이트 (트랜잭션 사용)"""
        profile = user.profile
        
        # 선호도 정보 업데이트
        if 'preferred_exercises' in preferences:
            profile.preferred_exercises = preferences['preferred_exercises']
        if 'preferred_foods' in preferences:
            profile.preferred_foods = preferences['preferred_foods']
        if 'disliked_exercises' in preferences:
            profile.disliked_exercises = preferences['disliked_exercises']
        if 'disliked_foods' in preferences:
            profile.disliked_foods = preferences['disliked_foods']
        
        profile.save(update_fields=[
            'preferred_exercises', 'preferred_foods',
            'disliked_exercises', 'disliked_foods', 'updated_at'
        ])
        
        return profile
    
    @staticmethod
    def get_user_recent_activities(user: User, limit: int = 10) -> List[Dict]:
        """최근 활동 조회 (운동 + 식단)"""
        # 최근 운동 기록
        recent_workouts = WorkoutLog.objects.filter(user=user).order_by('-date', '-created_at')[:limit]
        
        # 최근 식단 기록
        recent_diets = DietLog.objects.filter(user=user).order_by('-date', '-created_at')[:limit]
        
        # 활동 목록 통합 및 정렬
        activities = []
        
        for workout in recent_workouts:
            activities.append({
                'type': 'workout',
                'date': workout.date,
                'created_at': workout.created_at,
                'title': workout.workout_name,
                'details': {
                    'duration': workout.duration,
                    'calories': workout.calories_burned,
                    'type': workout.workout_type
                }
            })
        
        for diet in recent_diets:
            activities.append({
                'type': 'diet',
                'date': diet.date,
                'created_at': diet.created_at,
                'title': diet.get_meal_type_display(),
                'details': {
                    'calories': diet.total_calories,
                    'items': len(diet.food_items)
                }
            })
        
        # 날짜순 정렬
        activities.sort(key=lambda x: (x['date'], x['created_at']), reverse=True)
        
        return activities[:limit]
    
    @staticmethod
    def get_active_chat_session(user: User) -> Optional[ChatSession]:
        """활성 챗봇 세션 조회"""
        return ChatSession.objects.filter(
            user=user,
            is_active=True
        ).select_related('user').first()
    
    @staticmethod
    @transaction.atomic
    def create_chat_session(user: User) -> ChatSession:
        """새 챗봇 세션 생성"""
        # 기존 활성 세션 종료
        ChatSession.objects.filter(
            user=user,
            is_active=True
        ).update(
            is_active=False,
            ended_at=timezone.now()
        )
        
        # 새 세션 생성 (save 메소드에서 자동으로 user_session_number 부여)
        session = ChatSession.objects.create(user=user)
        return session
