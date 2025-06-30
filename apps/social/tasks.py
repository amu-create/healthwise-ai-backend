from celery import shared_task
from django.utils import timezone
from .models import Story
import logging

logger = logging.getLogger(__name__)


@shared_task
def delete_expired_stories():
    """만료된 스토리를 삭제하는 태스크"""
    try:
        # 만료된 스토리 찾기
        expired_stories = Story.objects.filter(
            expires_at__lte=timezone.now(),
            is_highlight=False  # 하이라이트는 삭제하지 않음
        )
        
        count = expired_stories.count()
        
        if count > 0:
            # 만료된 스토리 삭제
            expired_stories.delete()
            logger.info(f"Deleted {count} expired stories")
        
        return f"Deleted {count} expired stories"
    
    except Exception as e:
        logger.error(f"Error deleting expired stories: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def check_story_expiration():
    """곧 만료될 스토리에 대한 알림을 보내는 태스크 (옵션)"""
    try:
        from datetime import timedelta
        
        # 1시간 내에 만료될 스토리 찾기
        soon_to_expire = Story.objects.filter(
            expires_at__lte=timezone.now() + timedelta(hours=1),
            expires_at__gt=timezone.now(),
            is_highlight=False
        )
        
        for story in soon_to_expire:
            # 여기에 알림 로직 추가 가능
            pass
        
        return f"Checked {soon_to_expire.count()} stories"
    
    except Exception as e:
        logger.error(f"Error checking story expiration: {str(e)}")
        return f"Error: {str(e)}"
