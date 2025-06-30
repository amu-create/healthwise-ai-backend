from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import SocialProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """User 생성 시 자동으로 SocialProfile 생성"""
    if created:
        SocialProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """User 저장 시 SocialProfile도 저장"""
    try:
        instance.social_profile_obj.save()
    except:
        # 프로필이 없으면 생성
        SocialProfile.objects.create(user=instance)
