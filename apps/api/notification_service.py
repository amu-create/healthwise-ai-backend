from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
import json


class NotificationService:
    """알림 발송 서비스"""
    
    @staticmethod
    def send_achievement_notification(user, achievement, user_achievement):
        """업적 달성 알림 발송"""
        channel_layer = get_channel_layer()
        room_group_name = f'notifications_{user.id}'
        
        message = f'{achievement.get_name()}을(를) 달성했습니다! +{achievement.points}점'
        
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'achievement_notification',
                'achievement_id': achievement.id,
                'achievement_name': achievement.get_name(),
                'achievement_description': achievement.get_description(),
                'points': achievement.points,
                'badge_level': achievement.badge_level,
                'message': message,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    @staticmethod
    def send_level_up_notification(user, new_level, previous_level):
        """레벨업 알림 발송"""
        channel_layer = get_channel_layer()
        room_group_name = f'notifications_{user.id}'
        
        message = f'레벨 {new_level}로 상승했습니다!'
        
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'level_up_notification',
                'new_level': new_level,
                'previous_level': previous_level,
                'message': message,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    @staticmethod
    def send_follow_notification(follower, following):
        """팔로우 알림 발송"""
        channel_layer = get_channel_layer()
        room_group_name = f'notifications_{following.id}'
        
        follower_profile = getattr(follower, 'social_profile', None)
        profile_picture = follower_profile.profile_picture_url if follower_profile else None
        
        message = f'{follower.username}님이 당신을 팔로우했습니다'
        
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'follow_notification',
                'follower_id': follower.id,
                'follower_username': follower.username,
                'follower_profile_picture': profile_picture,
                'message': message,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    @staticmethod
    def send_like_notification(user, post):
        """좋아요 알림 발송"""
        if user == post.user:
            return  # 자기 게시물에 좋아요는 알림 안 함
        
        channel_layer = get_channel_layer()
        room_group_name = f'notifications_{post.user.id}'
        
        user_profile = getattr(user, 'social_profile', None)
        profile_picture = user_profile.profile_picture_url if user_profile else None
        
        content_preview = post.content[:50] + '...' if len(post.content) > 50 else post.content
        message = f'{user.username}님이 게시물을 좋아합니다'
        
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'like_notification',
                'user_id': user.id,
                'username': user.username,
                'profile_picture': profile_picture,
                'post_id': post.id,
                'content_preview': content_preview,
                'message': message,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    @staticmethod
    def send_comment_notification(user, comment):
        """댓글 알림 발송"""
        post = comment.post
        
        if user == post.user:
            return  # 자기 게시물에 댓글은 알림 안 함
        
        channel_layer = get_channel_layer()
        room_group_name = f'notifications_{post.user.id}'
        
        user_profile = getattr(user, 'social_profile', None)
        profile_picture = user_profile.profile_picture_url if user_profile else None
        
        content_preview = post.content[:50] + '...' if len(post.content) > 50 else post.content
        message = f'{user.username}님이 댓글을 남겼습니다'
        
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'comment_notification',
                'user_id': user.id,
                'username': user.username,
                'profile_picture': profile_picture,
                'post_id': post.id,
                'content_preview': content_preview,
                'comment_id': comment.id,
                'comment_content': comment.content,
                'message': message,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    @staticmethod
    def send_goal_achieved_notification(user, goal):
        """목표 달성 알림 발송"""
        channel_layer = get_channel_layer()
        room_group_name = f'notifications_{user.id}'
        
        message = f'{goal.get_goal_type_display()} 목표를 달성했습니다!'
        
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'goal_achieved_notification',
                'goal_type': goal.get_goal_type_display(),
                'target_value': goal.target_value,
                'achieved_value': goal.current_value,
                'message': message,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    @staticmethod
    def send_reminder_notification(user, reminder_type, message):
        """리마인더 알림 발송"""
        channel_layer = get_channel_layer()
        room_group_name = f'notifications_{user.id}'
        
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'reminder_notification',
                'reminder_type': reminder_type,
                'message': message,
                'timestamp': timezone.now().isoformat()
            }
        )
