from django.db import models
from apps.achievements.models import Achievement, UserAchievement


def check_workout_achievements(user, workout_result):
    """운동 결과에 따른 업적 체크"""
    new_achievements = []
    
    # 운동별 업적 체크
    exercise_achievements = {
        '푸시업': [
            ('pushup_first', '첫 푸시업', '푸시업을 처음으로 완료했습니다!', 10),
            ('pushup_master', '푸시업 마스터', '푸시업 평균 점수 90점 이상 달성!', 50),
            ('pushup_100', '푸시업 100개', '푸시업 100개 달성!', 30),
        ],
        '스쿼트': [
            ('squat_first', '첫 스쿼트', '스쿼트를 처음으로 완료했습니다!', 10),
            ('squat_master', '스쿼트 마스터', '스쿼트 평균 점수 90점 이상 달성!', 50),
            ('squat_100', '스쿼트 100개', '스쿼트 100개 달성!', 30),
        ],
        '플랭크': [
            ('plank_first', '첫 플랭크', '플랭크를 처음으로 완료했습니다!', 10),
            ('plank_30', '플랭크 30초', '플랭크 30초 유지 성공!', 20),
            ('plank_60', '플랭크 1분', '플랭크 1분 유지 성공!', 30),
            ('plank_120', '플랭크 2분', '플랭크 2분 유지 성공!', 50),
        ]
    }
    
    # 해당 운동의 업적 확인
    if workout_result.exercise_name in exercise_achievements:
        for achievement_code, title, description, points in exercise_achievements[workout_result.exercise_name]:
            # 업적이 이미 존재하는지 확인
            achievement, created = Achievement.objects.get_or_create(
                code=achievement_code,
                defaults={
                    'title': title,
                    'description': description,
                    'points': points,
                    'category': 'exercise',
                    'icon': '🏆'
                }
            )
            
            # 사용자가 이미 달성했는지 확인
            user_achievement, user_created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            
            if user_created:
                # 조건 확인
                should_unlock = False
                
                if 'first' in achievement_code:
                    # 첫 운동 완료
                    should_unlock = True
                elif 'master' in achievement_code:
                    # 마스터 레벨 (90점 이상)
                    should_unlock = workout_result.average_score >= 90
                elif achievement_code == 'pushup_100' or achievement_code == 'squat_100':
                    # 100개 달성
                    should_unlock = workout_result.rep_count >= 100
                elif achievement_code == 'plank_30':
                    should_unlock = workout_result.duration >= 30
                elif achievement_code == 'plank_60':
                    should_unlock = workout_result.duration >= 60
                elif achievement_code == 'plank_120':
                    should_unlock = workout_result.duration >= 120
                
                if should_unlock:
                    user_achievement.is_unlocked = True
                    user_achievement.save()
                    new_achievements.append({
                        'title': achievement.title,
                        'description': achievement.description,
                        'points': achievement.points,
                        'icon': achievement.icon
                    })
                else:
                    # 조건을 만족하지 않으면 삭제
                    user_achievement.delete()
    
    # 전체 운동 관련 업적
    total_workouts = user.workout_results.count()
    
    general_achievements = [
        ('workout_1', '운동 시작!', '첫 운동을 완료했습니다!', 10),
        ('workout_10', '운동 습관', '10번의 운동을 완료했습니다!', 20),
        ('workout_50', '운동 마니아', '50번의 운동을 완료했습니다!', 50),
        ('workout_100', '운동 중독자', '100번의 운동을 완료했습니다!', 100),
        ('perfect_score', '완벽한 자세', '평균 점수 95점 이상을 달성했습니다!', 30),
        ('calorie_100', '칼로리 버너', '한 번의 운동으로 100kcal 이상 소모!', 20),
        ('calorie_500', '칼로리 파괴자', '한 번의 운동으로 500kcal 이상 소모!', 50),
    ]
    
    for achievement_code, title, description, points in general_achievements:
        achievement, created = Achievement.objects.get_or_create(
            code=achievement_code,
            defaults={
                'title': title,
                'description': description,
                'points': points,
                'category': 'general',
                'icon': '🏅'
            }
        )
        
        # 달성 여부 확인
        should_unlock = False
        
        if achievement_code == 'workout_1' and total_workouts >= 1:
            should_unlock = True
        elif achievement_code == 'workout_10' and total_workouts >= 10:
            should_unlock = True
        elif achievement_code == 'workout_50' and total_workouts >= 50:
            should_unlock = True
        elif achievement_code == 'workout_100' and total_workouts >= 100:
            should_unlock = True
        elif achievement_code == 'perfect_score' and workout_result.average_score >= 95:
            should_unlock = True
        elif achievement_code == 'calorie_100' and workout_result.calories_burned >= 100:
            should_unlock = True
        elif achievement_code == 'calorie_500' and workout_result.calories_burned >= 500:
            should_unlock = True
        
        if should_unlock:
            user_achievement, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement,
                defaults={'is_unlocked': True}
            )
            
            if created or not user_achievement.is_unlocked:
                user_achievement.is_unlocked = True
                user_achievement.save()
                new_achievements.append({
                    'title': achievement.title,
                    'description': achievement.description,
                    'points': achievement.points,
                    'icon': achievement.icon
                })
    
    # 일일 스트릭 업적
    from datetime import timedelta
    from django.utils import timezone
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # 오늘 운동했는지 확인
    today_workouts = user.workout_results.filter(created_at__date=today).count()
    yesterday_workouts = user.workout_results.filter(created_at__date=yesterday).count()
    
    if today_workouts > 0 and yesterday_workouts > 0:
        # 연속 운동 일수 계산
        consecutive_days = 1
        check_date = yesterday
        
        while True:
            check_date -= timedelta(days=1)
            if user.workout_results.filter(created_at__date=check_date).exists():
                consecutive_days += 1
            else:
                break
        
        streak_achievements = [
            ('streak_3', '3일 연속!', '3일 연속 운동을 완료했습니다!', 15),
            ('streak_7', '일주일 달성!', '7일 연속 운동을 완료했습니다!', 30),
            ('streak_30', '한 달 달성!', '30일 연속 운동을 완료했습니다!', 100),
        ]
        
        for achievement_code, title, description, points in streak_achievements:
            if (achievement_code == 'streak_3' and consecutive_days >= 3) or \
               (achievement_code == 'streak_7' and consecutive_days >= 7) or \
               (achievement_code == 'streak_30' and consecutive_days >= 30):
                
                achievement, created = Achievement.objects.get_or_create(
                    code=achievement_code,
                    defaults={
                        'title': title,
                        'description': description,
                        'points': points,
                        'category': 'streak',
                        'icon': '🔥'
                    }
                )
                
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={'is_unlocked': True}
                )
                
                if created or not user_achievement.is_unlocked:
                    user_achievement.is_unlocked = True
                    user_achievement.save()
                    new_achievements.append({
                        'title': achievement.title,
                        'description': achievement.description,
                        'points': achievement.points,
                        'icon': achievement.icon
                    })
    
    return new_achievements
