from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


def send_notification_to_user(user_id, notification_data):
    """Send real-time notification to user via WebSocket"""
    try:
        channel_layer = get_channel_layer()
        room_group_name = f"notifications_{user_id}"
        
        # Send notification to WebSocket group
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "notification_message",
                "notification": notification_data
            }
        )
        logger.info(f"Sent notification to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}")


def send_achievement_to_user(user_id, achievement_data):
    """Send achievement unlock notification to user via WebSocket"""
    try:
        channel_layer = get_channel_layer()
        room_group_name = f"notifications_{user_id}"
        
        # Send achievement to WebSocket group
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "achievement_unlocked",
                "achievement": achievement_data
            }
        )
        logger.info(f"Sent achievement notification to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send achievement notification to user {user_id}: {e}")


def send_level_up_to_user(user_id, level):
    """Send level up notification to user via WebSocket"""
    try:
        channel_layer = get_channel_layer()
        room_group_name = f"notifications_{user_id}"
        
        # Send level up to WebSocket group
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "level_up",
                "level": level
            }
        )
        logger.info(f"Sent level up notification to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send level up notification to user {user_id}: {e}")
