from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    User가 생성될 때 자동으로 UserProfile을 생성합니다.
    """
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    User가 저장될 때 연결된 UserProfile도 저장합니다.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
