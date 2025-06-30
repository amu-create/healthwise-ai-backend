from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.api.models import Achievement, UserAchievement, WorkoutRoutineLog, FoodAnalysis
from django.db.models import Count
import random

User = get_user_model()


class Command(BaseCommand):
    help = '모든 사용자에게 기본 업적 할당 및 일부 진행률 설정'

    def handle(self, *args, **options):
        users = User.objects.all()
        achievements = Achievement.objects.all()
        
        created_count = 0
        
        for user in users:
            # 각 사용자의 실제 데이터 기반으로 업적 진행률 계산
            workout_count = WorkoutRoutineLog.objects.filter(user=user).count()
            food_count = FoodAnalysis.objects.filter(user=user).count()
            
            for achievement in achievements:
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={'progress': 0}
                )
                
                if created:
                    created_count += 1
                    
                    # 실제 데이터 기반 진행률 설정
                    if achievement.category == 'workout':
                        if 'First Step' in achievement.name_en or '첫 걸음' in achievement.name:
                            user_achievement.progress = min(workout_count, 1)
                        elif 'Workout Addict' in achievement.name_en or '운동 중독자' in achievement.name:
                            user_achievement.progress = min(workout_count, achievement.target_value)
                        elif 'Fitness Warrior' in achievement.name_en or '피트니스 전사' in achievement.name:
                            user_achievement.progress = min(workout_count, achievement.target_value)
                        elif 'King of Exercise' in achievement.name_en or '운동의 왕' in achievement.name:
                            user_achievement.progress = min(workout_count, achievement.target_value)
                        else:
                            # 랜덤 진행률 (0~80%)
                            user_achievement.progress = random.randint(0, int(achievement.target_value * 0.8))
                    
                    elif achievement.category == 'nutrition':
                        if 'Nutrition Start' in achievement.name_en or '영양 관리 시작' in achievement.name:
                            user_achievement.progress = min(food_count, 1)
                        elif 'Balanced Diet' in achievement.name_en or '균형 잡힌 식단' in achievement.name:
                            user_achievement.progress = min(food_count, achievement.target_value)
                        else:
                            # 랜덤 진행률 (0~60%)
                            user_achievement.progress = random.randint(0, int(achievement.target_value * 0.6))
                    
                    elif achievement.category == 'streak':
                        # 연속 기록은 낮은 진행률
                        user_achievement.progress = random.randint(0, min(3, achievement.target_value))
                    
                    elif achievement.category == 'milestone':
                        # 마일스톤은 중간 정도 진행률
                        user_achievement.progress = random.randint(0, int(achievement.target_value * 0.5))
                    
                    elif achievement.category == 'challenge':
                        # 챌린지는 낮은 진행률
                        user_achievement.progress = random.randint(0, int(achievement.target_value * 0.3))
                    
                    # 목표 달성 체크
                    if user_achievement.progress >= achievement.target_value:
                        user_achievement.completed = True
                        user_achievement.completed_at = user.date_joined  # 가입일로 설정
                    
                    user_achievement.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'{user.username} - {achievement.name}: {user_achievement.progress}/{achievement.target_value}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'총 {created_count}개의 사용자 업적이 생성되었습니다.'
            )
        )
