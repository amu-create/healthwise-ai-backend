from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from ..models import Achievement, UserAchievement, UserLevel, WorkoutRoutineLog, FoodAnalysis, DailyNutrition
from django.contrib.auth import get_user_model

User = get_user_model()


class AchievementService:
    """업적 시스템 관리 서비스"""
    
    @staticmethod
    def check_and_update_achievements(user):
        """사용자의 모든 업적 진행상황을 체크하고 업데이트"""
        achievements_updated = []
        level_service = LevelService()
        
        # 운동 관련 업적 체크
        achievements_updated.extend(AchievementService._check_workout_achievements(user))
        
        # 영양 관련 업적 체크
        achievements_updated.extend(AchievementService._check_nutrition_achievements(user))
        
        # 연속 출석 업적 체크
        achievements_updated.extend(AchievementService._check_streak_achievements(user))
        
        # 업적 완료로 인한 경험치 추가
        for achievement in achievements_updated:
            if achievement.completed and achievement.completed_at:
                # 새로 완료된 업적에 대해서만 경험치 추가
                if achievement.updated_at >= timezone.now() - timedelta(seconds=5):
                    level_service.add_achievement_points(user, achievement.achievement.points)
        
        return achievements_updated
    
    @staticmethod
    def _check_workout_achievements(user):
        """운동 관련 업적 체크"""
        updated = []
        
        # 총 운동 횟수 관련 업적
        total_workouts = WorkoutRoutineLog.objects.filter(user=user).count()
        workout_achievements = Achievement.objects.filter(
            category='workout',
            name__contains='운동'
        )
        
        for achievement in workout_achievements:
            user_achievement, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            
            if not user_achievement.completed:
                user_achievement.progress = total_workouts
                if user_achievement.progress >= achievement.target_value:
                    user_achievement.completed = True
                    user_achievement.completed_at = timezone.now()
                user_achievement.save()
                updated.append(user_achievement)
        
        return updated
    
    @staticmethod
    def _check_nutrition_achievements(user):
        """영양 관련 업적 체크"""
        updated = []
        
        # 식단 기록 횟수 관련 업적
        total_food_logs = FoodAnalysis.objects.filter(user=user).count()
        nutrition_achievements = Achievement.objects.filter(
            category='nutrition',
            name__contains='식단'
        )
        
        for achievement in nutrition_achievements:
            user_achievement, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            
            if not user_achievement.completed:
                user_achievement.progress = total_food_logs
                if user_achievement.progress >= achievement.target_value:
                    user_achievement.completed = True
                    user_achievement.completed_at = timezone.now()
                user_achievement.save()
                updated.append(user_achievement)
        
        return updated
    
    @staticmethod
    def _check_streak_achievements(user):
        """연속 출석 관련 업적 체크"""
        updated = []
        
        # 최근 운동 기록으로 연속 일수 계산
        workout_logs = WorkoutRoutineLog.objects.filter(user=user).order_by('-date')
        
        if workout_logs.exists():
            streak = 1
            last_date = workout_logs.first().date
            
            for log in workout_logs[1:]:
                if (last_date - log.date).days == 1:
                    streak += 1
                    last_date = log.date
                else:
                    break
            
            # 연속 출석 업적 체크
            streak_achievements = Achievement.objects.filter(category='streak')
            
            for achievement in streak_achievements:
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                
                if not user_achievement.completed:
                    user_achievement.progress = streak
                    if user_achievement.progress >= achievement.target_value:
                        user_achievement.completed = True
                        user_achievement.completed_at = timezone.now()
                    user_achievement.save()
                    updated.append(user_achievement)
        
        return updated
    
    @staticmethod
    def create_initial_achievements():
        """초기 업적 데이터 생성"""
        achievements_data = [
            # 운동 업적
            {
                'name': '첫 운동',
                'name_en': 'First Workout',
                'name_es': 'Primer Entrenamiento',
                'description': '첫 번째 운동을 완료했습니다!',
                'description_en': 'Completed your first workout!',
                'description_es': '¡Completaste tu primer entrenamiento!',
                'category': 'workout',
                'badge_level': 'bronze',
                'icon_name': 'fitness_center',
                'target_value': 1,
                'points': 10
            },
            {
                'name': '운동 초보자',
                'name_en': 'Workout Beginner',
                'name_es': 'Principiante de Ejercicio',
                'description': '10회 운동을 완료했습니다!',
                'description_en': 'Completed 10 workouts!',
                'description_es': '¡Completaste 10 entrenamientos!',
                'category': 'workout',
                'badge_level': 'silver',
                'icon_name': 'emoji_events',
                'target_value': 10,
                'points': 30
            },
            {
                'name': '운동 마스터',
                'name_en': 'Workout Master',
                'name_es': 'Maestro del Ejercicio',
                'description': '50회 운동을 완료했습니다!',
                'description_en': 'Completed 50 workouts!',
                'description_es': '¡Completaste 50 entrenamientos!',
                'category': 'workout',
                'badge_level': 'gold',
                'icon_name': 'military_tech',
                'target_value': 50,
                'points': 100
            },
            # 영양 업적
            {
                'name': '첫 식단 기록',
                'name_en': 'First Meal Log',
                'name_es': 'Primer Registro de Comida',
                'description': '첫 번째 식단을 기록했습니다!',
                'description_en': 'Logged your first meal!',
                'description_es': '¡Registraste tu primera comida!',
                'category': 'nutrition',
                'badge_level': 'bronze',
                'icon_name': 'restaurant',
                'target_value': 1,
                'points': 10
            },
            {
                'name': '영양 관리자',
                'name_en': 'Nutrition Manager',
                'name_es': 'Gestor de Nutrición',
                'description': '30회 식단을 기록했습니다!',
                'description_en': 'Logged 30 meals!',
                'description_es': '¡Registraste 30 comidas!',
                'category': 'nutrition',
                'badge_level': 'silver',
                'icon_name': 'local_dining',
                'target_value': 30,
                'points': 50
            },
            # 연속 출석 업적
            {
                'name': '3일 연속',
                'name_en': '3 Day Streak',
                'name_es': 'Racha de 3 Días',
                'description': '3일 연속 운동했습니다!',
                'description_en': 'Worked out 3 days in a row!',
                'description_es': '¡Entrenaste 3 días seguidos!',
                'category': 'streak',
                'badge_level': 'bronze',
                'icon_name': 'whatshot',
                'target_value': 3,
                'points': 20
            },
            {
                'name': '일주일 전사',
                'name_en': 'Week Warrior',
                'name_es': 'Guerrero Semanal',
                'description': '7일 연속 운동했습니다!',
                'description_en': 'Worked out 7 days in a row!',
                'description_es': '¡Entrenaste 7 días seguidos!',
                'category': 'streak',
                'badge_level': 'silver',
                'icon_name': 'local_fire_department',
                'target_value': 7,
                'points': 50
            },
            {
                'name': '한달 챔피언',
                'name_en': 'Month Champion',
                'name_es': 'Campeón del Mes',
                'description': '30일 연속 운동했습니다!',
                'description_en': 'Worked out 30 days in a row!',
                'description_es': '¡Entrenaste 30 días seguidos!',
                'category': 'streak',
                'badge_level': 'gold',
                'icon_name': 'stars',
                'target_value': 30,
                'points': 150
            },
        ]
        
        created_count = 0
        for data in achievements_data:
            achievement, created = Achievement.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if created:
                created_count += 1
        
        return created_count


class LevelService:
    """레벨 시스템 관리 서비스"""
    
    @staticmethod
    def get_or_create_user_level(user):
        """사용자 레벨 정보 가져오기 또는 생성"""
        user_level, created = UserLevel.objects.get_or_create(
            user=user,
            defaults={'level': 1, 'experience_points': 0}
        )
        return user_level
    
    @staticmethod
    def add_achievement_points(user, points):
        """업적 포인트 추가 및 레벨업 처리"""
        user_level = LevelService.get_or_create_user_level(user)
        user_level.total_achievement_points += points
        
        # 경험치로 변환 (업적 포인트 = 경험치)
        old_level = user_level.level
        new_level = user_level.add_experience(points)
        
        # 레벨업 했다면 알림 생성 (추후 구현)
        if new_level > old_level:
            # TODO: 레벨업 알림 생성
            pass
        
        return user_level
    
    @staticmethod
    def set_main_achievements(user, achievement_ids):
        """대표 업적 설정"""
        user_level = LevelService.get_or_create_user_level(user)
        user_level.set_main_achievements(achievement_ids)
        return user_level
    
    @staticmethod
    def get_level_info(user):
        """사용자 레벨 정보 조회"""
        user_level = LevelService.get_or_create_user_level(user)
        
        return {
            'level': user_level.level,
            'experience_points': user_level.experience_points,
            'total_achievement_points': user_level.total_achievement_points,
            'current_level_progress': user_level.current_level_progress,
            'required_exp_for_next_level': user_level.required_exp_for_next_level,
            'main_achievements': [
                {
                    'id': ua.id,
                    'achievement': {
                        'name': ua.achievement.name,
                        'description': ua.achievement.description,
                        'icon_name': ua.achievement.icon_name,
                        'badge_level': ua.achievement.badge_level,
                        'category': ua.achievement.category
                    }
                }
                for ua in user_level.main_achievements.all()
            ]
        }
