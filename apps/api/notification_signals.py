from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.api.models import (
    WorkoutRoutineLog, DailyNutrition, FoodAnalysis, UserProfile, 
    WorkoutAchievement, UserWorkoutAchievement
)
from django.db import models
from apps.social.models import SocialPost, SocialComment, SocialProfile
from apps.api.notifications import (
    WorkoutNotificationService,
    NutritionNotificationService,
    HealthNotificationService,
    CommunityNotificationService,
    AINotificationService,
    MotivationNotificationService,
    SystemNotificationService
)

import logging

logger = logging.getLogger(__name__)
User = get_user_model()


# 운동 관련 시그널
@receiver(post_save, sender=WorkoutRoutineLog)
def workout_completed_notification(sender, instance, created, **kwargs):
    """운동 완료 시 알림"""
    if created:  # completed_at 체크 제거 - WorkoutRoutineLog 모델에는 이 필드가 없음
        try:
            # 운동 완료 알림
            WorkoutNotificationService.send_workout_completed_notification(
                user=instance.user,
                workout_log=instance
            )
            
            # 주간 운동 목표 체크
            weekly_workouts = WorkoutRoutineLog.objects.filter(
                user=instance.user,
                date__gte=timezone.now().date() - timedelta(days=7)
            ).count()
            
            # 사용자의 fitness_profile에서 목표 확인
            user_profile = getattr(instance.user, 'fitness_profile', None)
            if user_profile and hasattr(user_profile, 'frequency') and user_profile.frequency > 0:
                WorkoutNotificationService.send_workout_goal_progress(
                    user=instance.user,
                    goal_type='weekly_workouts',
                    current_value=weekly_workouts,
                    target_value=user_profile.frequency
                )
        except Exception as e:
            logger.error(f"Error sending workout notification: {e}")


# 영양 관련 시그널
@receiver(post_save, sender=FoodAnalysis)
def nutrition_log_notification(sender, instance, created, **kwargs):
    """영양 기록 시 알림"""
    if created:
        try:
            # 일일 칼로리 체크
            today = timezone.now().date()
            daily_calories = FoodAnalysis.objects.filter(
                user=instance.user,
                analyzed_at__date=today
            ).aggregate(
                total_calories=models.Sum('calories')
            )['total_calories'] or 0
            
            user_profile = getattr(instance.user, 'fitness_profile', None)
            if user_profile and hasattr(user_profile, 'daily_calorie_goal'):
                NutritionNotificationService.send_calorie_goal_notification(
                    user=instance.user,
                    current_calories=daily_calories,
                    target_calories=user_profile.daily_calorie_goal
                )
        except Exception as e:
            logger.error(f"Error sending nutrition notification: {e}")


# 프로필 관련 시그널
@receiver(post_save, sender=UserProfile)
def profile_update_notification(sender, instance, created, **kwargs):
    """프로필 업데이트 시 알림"""
    if not created:
        try:
            # 프로필 완성도 체크
            completion_fields = [
                instance.birth_date,
                instance.height,
                instance.weight,
                instance.fitness_goals,
                instance.profile_picture
            ]
            completed = sum(1 for field in completion_fields if field)
            completion_percentage = int((completed / len(completion_fields)) * 100)
            
            if completion_percentage < 80:
                SystemNotificationService.send_profile_completion_reminder(
                    user=instance.user,
                    completion_percentage=completion_percentage
                )
                
            # 체중 변화 체크
            if hasattr(instance, '_weight_changed') and instance._weight_changed:
                previous_weight = instance._previous_weight
                if previous_weight and abs(instance.weight - previous_weight) >= 0.5:
                    HealthNotificationService.send_weight_change_notification(
                        user=instance.user,
                        current_weight=instance.weight,
                        previous_weight=previous_weight
                    )
        except Exception as e:
            logger.error(f"Error sending profile notification: {e}")


@receiver(pre_save, sender=UserProfile)
def track_weight_change(sender, instance, **kwargs):
    """체중 변화 추적을 위한 pre_save 시그널"""
    if instance.pk:
        try:
            previous = UserProfile.objects.get(pk=instance.pk)
            if previous.weight != instance.weight:
                instance._weight_changed = True
                instance._previous_weight = previous.weight
        except UserProfile.DoesNotExist:
            pass


# 업적 관련 시그널
@receiver(post_save, sender=UserWorkoutAchievement)
def achievement_unlocked_notification(sender, instance, created, **kwargs):
    """업적 달성 시 알림"""
    if created:
        try:
            from apps.api.notification_service_v2 import NotificationService
            NotificationService.send_achievement_notification(
                user=instance.user,
                achievement=instance.achievement,
                user_achievement=instance
            )
        except Exception as e:
            logger.error(f"Error sending achievement notification: {e}")


# 소셜 관련 시그널
@receiver(post_save, sender=SocialComment)
def comment_notification(sender, instance, created, **kwargs):
    """댓글 작성 시 알림"""
    if created:
        try:
            from apps.api.notification_service_v2 import NotificationService
            NotificationService.send_comment_notification(
                user=instance.user,
                comment=instance
            )
        except Exception as e:
            logger.error(f"Error sending comment notification: {e}")


# 팔로우 관련 시그널 (M2M 변경)
@receiver(models.signals.m2m_changed, sender=SocialProfile.followers.through)
def follow_notification(sender, instance, action, pk_set, **kwargs):
    """팔로우/언팔로우 시 알림"""
    if action == "post_add" and pk_set:
        try:
            from apps.api.notification_service_v2 import NotificationService
            for follower_id in pk_set:
                follower = User.objects.get(pk=follower_id)
                NotificationService.send_follow_notification(
                    follower=follower,
                    following=instance.user
                )
        except Exception as e:
            logger.error(f"Error sending follow notification: {e}")


# 좋아요 관련 시그널 (M2M 변경)
@receiver(models.signals.m2m_changed, sender=SocialPost.likes.through)
def like_notification(sender, instance, action, pk_set, **kwargs):
    """좋아요 시 알림"""
    if action == "post_add" and pk_set:
        try:
            from apps.api.notification_service_v2 import NotificationService
            for user_id in pk_set:
                user = User.objects.get(pk=user_id)
                NotificationService.send_like_notification(
                    user=user,
                    post=instance
                )
        except Exception as e:
            logger.error(f"Error sending like notification: {e}")


# 주기적 알림을 위한 Celery 태스크 (선택적)
# celery_tasks.py에 구현 가능
"""
from celery import shared_task
from datetime import datetime

@shared_task
def send_daily_motivation():
    '''매일 아침 동기부여 메시지 발송'''
    active_users = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(days=7)
    )
    
    for user in active_users:
        MotivationNotificationService.send_daily_motivation(user)


@shared_task
def send_workout_reminders():
    '''설정된 시간에 운동 리마인더 발송'''
    current_time = timezone.now().time()
    profiles = UserProfile.objects.filter(
        workout_reminder_time__hour=current_time.hour,
        workout_reminder_time__minute=current_time.minute,
        workout_reminder_enabled=True
    )
    
    for profile in profiles:
        WorkoutNotificationService.send_workout_reminder(
            user=profile.user,
            scheduled_time=profile.workout_reminder_time
        )


@shared_task
def send_meal_reminders():
    '''식사 시간 리마인더 발송'''
    current_hour = timezone.now().hour
    
    meal_times = {
        8: 'breakfast',
        12: 'lunch',
        18: 'dinner',
    }
    
    if current_hour in meal_times:
        meal_type = meal_times[current_hour]
        users = User.objects.filter(
            profile__meal_reminder_enabled=True
        )
        
        for user in users:
            NutritionNotificationService.send_meal_reminder(
                user=user,
                meal_type=meal_type
            )
"""
