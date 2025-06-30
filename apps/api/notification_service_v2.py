from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import Notification, UserWorkoutLevel
import json
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """알림 발송 서비스 (다국어 지원)"""
    
    @staticmethod
    def create_notification(user, notification_type, title_ko, title_en, title_es,
                          message_ko, message_en, message_es,
                          metadata=None, action_url=None):
        """알림 생성 및 저장"""
        try:
            notification = Notification.objects.create(
                user=user,
                type=notification_type,
                title=title_ko,
                title_en=title_en,
                title_es=title_es,
                message=message_ko,
                message_en=message_en,
                message_es=message_es,
                metadata=metadata or {},
                action_url=action_url
            )
            return notification
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return None
    
    @staticmethod
    def send_realtime_notification(user, notification_data):
        """WebSocket을 통한 실시간 알림 전송"""
        try:
            channel_layer = get_channel_layer()
            room_group_name = f'notifications_{user.id}'
            
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                notification_data
            )
        except Exception as e:
            logger.error(f"Failed to send realtime notification: {e}")
    
    @staticmethod
    def send_achievement_notification(user, achievement, user_achievement):
        """업적 달성 알림 발송"""
        # 알림 저장
        notification = NotificationService.create_notification(
            user=user,
            notification_type='achievement',
            title_ko=f'{achievement.name} 업적 달성!',
            title_en=f'{achievement.name_en or achievement.name} Achievement Unlocked!',
            title_es=f'¡Logro {achievement.name_es or achievement.name} Desbloqueado!',
            message_ko=f'{achievement.description}을(를) 달성했습니다! +{achievement.points}점',
            message_en=f'You achieved {achievement.description_en or achievement.description}! +{achievement.points} points',
            message_es=f'¡Has logrado {achievement.description_es or achievement.description}! +{achievement.points} puntos',
            metadata={
                'icon': 'achievement',
                'achievement_id': achievement.id,
                'badge_level': achievement.badge_level,
                'points': achievement.points
            },
            action_url='/achievements'
        )
        
        # 실시간 전송
        NotificationService.send_realtime_notification(user, {
            'type': 'achievement_unlocked',
            'achievement': {
                'name': achievement.name,
                'name_en': achievement.name_en,
                'name_es': achievement.name_es,
                'badge_level': achievement.badge_level,
                'points': achievement.points
            },
            'animation': True
        })
        
        # 레벨업 체크
        user_level = user.workout_level_info
        old_level = user_level.level
        user_level.add_experience(achievement.points)
        
        if user_level.level > old_level:
            NotificationService.send_level_up_notification(user, user_level.level, old_level)
    
    @staticmethod
    def send_level_up_notification(user, new_level, previous_level):
        """레벨업 알림 발송"""
        level_titles = {
            1: ('초보자', 'Beginner', 'Principiante'),
            5: ('견습생', 'Apprentice', 'Aprendiz'),
            10: ('수련생', 'Trainee', 'Entrenador'),
            20: ('전사', 'Warrior', 'Guerrero'),
            30: ('베테랑', 'Veteran', 'Veterano'),
            40: ('엘리트', 'Elite', 'Élite'),
            50: ('마스터', 'Master', 'Maestro'),
            60: ('그랜드마스터', 'Grandmaster', 'Gran Maestro'),
            70: ('챔피언', 'Champion', 'Campeón'),
            80: ('레전드', 'Legend', 'Leyenda'),
            90: ('신화', 'Mythic', 'Mítico'),
            100: ('전설의 존재', 'Legendary', 'Legendario'),
        }
        
        # 현재 레벨의 타이틀 찾기
        title_ko, title_en, title_es = '초보자', 'Beginner', 'Principiante'
        for level, titles in sorted(level_titles.items(), reverse=True):
            if new_level >= level:
                title_ko, title_en, title_es = titles
                break
        
        # 알림 저장
        notification = NotificationService.create_notification(
            user=user,
            notification_type='achievement',
            title_ko='레벨업!',
            title_en='Level Up!',
            title_es='¡Subida de Nivel!',
            message_ko=f'레벨 {new_level}에 도달했습니다! 이제 {title_ko}입니다.',
            message_en=f'You reached level {new_level}! You are now {title_en}.',
            message_es=f'¡Alcanzaste el nivel {new_level}! Ahora eres {title_es}.',
            metadata={
                'icon': 'level_up',
                'new_level': new_level,
                'previous_level': previous_level,
                'title': title_ko
            },
            action_url='/achievements'
        )
        
        # 실시간 전송
        NotificationService.send_realtime_notification(user, {
            'type': 'level_up',
            'level': new_level,
            'title': title_ko,
            'animation': True
        })
    
    @staticmethod
    def send_follow_notification(follower, following):
        """팔로우 알림 발송"""
        follower_profile = getattr(follower, 'social_profile', None)
        
        notification = NotificationService.create_notification(
            user=following,
            notification_type='social',
            title_ko='새로운 팔로워',
            title_en='New Follower',
            title_es='Nuevo Seguidor',
            message_ko=f'{follower.username}님이 당신을 팔로우했습니다',
            message_en=f'{follower.username} started following you',
            message_es=f'{follower.username} comenzó a seguirte',
            metadata={
                'icon': 'follow',
                'follower_id': follower.id,
                'follower_username': follower.username,
                'follower_profile_picture': follower_profile.profile_picture_url if follower_profile else None
            },
            action_url=f'/profile/{follower.username}'
        )
        
        # 실시간 전송
        NotificationService.send_realtime_notification(following, {
            'type': 'notification',
            'notification': {
                'id': notification.id,
                'type': notification.type,
                'title': notification.title,
                'title_en': notification.title_en,
                'title_es': notification.title_es,
                'message': notification.message,
                'message_en': notification.message_en,
                'message_es': notification.message_es,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'metadata': notification.metadata,
                'action_url': notification.action_url,
            }
        })
    
    @staticmethod
    def send_like_notification(user, post):
        """좋아요 알림 발송"""
        if user == post.user:
            return  # 자기 게시물에 좋아요는 알림 안 함
        
        user_profile = getattr(user, 'social_profile', None)
        content_preview = post.content[:50] + '...' if len(post.content) > 50 else post.content
        
        notification = NotificationService.create_notification(
            user=post.user,
            notification_type='social',
            title_ko='게시물 좋아요',
            title_en='Post Liked',
            title_es='Me Gusta en Publicación',
            message_ko=f'{user.username}님이 회원님의 게시물을 좋아합니다',
            message_en=f'{user.username} liked your post',
            message_es=f'A {user.username} le gustó tu publicación',
            metadata={
                'icon': 'like',
                'user_id': user.id,
                'username': user.username,
                'profile_picture': user_profile.profile_picture_url if user_profile else None,
                'post_id': post.id,
                'content_preview': content_preview
            },
            action_url=f'/social/post/{post.id}'
        )
        
        # 실시간 전송
        NotificationService.send_realtime_notification(post.user, {
            'type': 'notification',
            'notification': {
                'id': notification.id,
                'type': notification.type,
                'title': notification.title,
                'title_en': notification.title_en,
                'title_es': notification.title_es,
                'message': notification.message,
                'message_en': notification.message_en,
                'message_es': notification.message_es,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'metadata': notification.metadata,
                'action_url': notification.action_url,
            }
        })
    
    @staticmethod
    def send_comment_notification(user, comment):
        """댓글 알림 발송"""
        post = comment.post
        
        if user == post.user:
            return  # 자기 게시물에 댓글은 알림 안 함
        
        user_profile = getattr(user, 'social_profile', None)
        content_preview = post.content[:50] + '...' if len(post.content) > 50 else post.content
        
        notification = NotificationService.create_notification(
            user=post.user,
            notification_type='social',
            title_ko='새로운 댓글',
            title_en='New Comment',
            title_es='Nuevo Comentario',
            message_ko=f'{user.username}님이 댓글을 남겼습니다: {comment.content[:30]}...',
            message_en=f'{user.username} commented: {comment.content[:30]}...',
            message_es=f'{user.username} comentó: {comment.content[:30]}...',
            metadata={
                'icon': 'comment',
                'user_id': user.id,
                'username': user.username,
                'profile_picture': user_profile.profile_picture_url if user_profile else None,
                'post_id': post.id,
                'comment_id': comment.id,
                'content_preview': content_preview
            },
            action_url=f'/social/post/{post.id}'
        )
        
        # 실시간 전송
        NotificationService.send_realtime_notification(post.user, {
            'type': 'notification',
            'notification': {
                'id': notification.id,
                'type': notification.type,
                'title': notification.title,
                'title_en': notification.title_en,
                'title_es': notification.title_es,
                'message': notification.message,
                'message_en': notification.message_en,
                'message_es': notification.message_es,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'metadata': notification.metadata,
                'action_url': notification.action_url,
            }
        })
    
    @staticmethod
    def send_goal_achieved_notification(user, goal):
        """목표 달성 알림 발송"""
        goal_names = {
            'daily_calories': ('일일 칼로리 목표', 'Daily Calorie Goal', 'Meta de Calorías Diarias'),
            'weekly_workouts': ('주간 운동 목표', 'Weekly Workout Goal', 'Meta de Ejercicio Semanal'),
            'monthly_workouts': ('월간 운동 목표', 'Monthly Workout Goal', 'Meta de Ejercicio Mensual'),
            'weight_target': ('목표 체중', 'Weight Target', 'Peso Objetivo'),
            'daily_steps': ('일일 걸음수 목표', 'Daily Steps Goal', 'Meta de Pasos Diarios'),
            'daily_water': ('일일 수분 섭취 목표', 'Daily Water Goal', 'Meta de Agua Diaria'),
            'sleep_hours': ('수면 시간 목표', 'Sleep Hours Goal', 'Meta de Horas de Sueño'),
        }
        
        goal_name_ko, goal_name_en, goal_name_es = goal_names.get(
            goal.goal_type, 
            ('목표', 'Goal', 'Meta')
        )
        
        notification = NotificationService.create_notification(
            user=user,
            notification_type='achievement',
            title_ko='목표 달성!',
            title_en='Goal Achieved!',
            title_es='¡Meta Lograda!',
            message_ko=f'{goal_name_ko}를 달성했습니다! ({goal.current_value}/{goal.target_value})',
            message_en=f'You achieved your {goal_name_en}! ({goal.current_value}/{goal.target_value})',
            message_es=f'¡Lograste tu {goal_name_es}! ({goal.current_value}/{goal.target_value})',
            metadata={
                'icon': 'achievement',
                'goal_type': goal.goal_type,
                'target_value': goal.target_value,
                'achieved_value': goal.current_value
            },
            action_url='/achievements'
        )
        
        # 실시간 전송
        NotificationService.send_realtime_notification(user, {
            'type': 'notification',
            'notification': {
                'id': notification.id,
                'type': notification.type,
                'title': notification.title,
                'title_en': notification.title_en,
                'title_es': notification.title_es,
                'message': notification.message,
                'message_en': notification.message_en,
                'message_es': notification.message_es,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'metadata': notification.metadata,
                'action_url': notification.action_url,
            }
        })
