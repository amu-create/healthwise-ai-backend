# 스토리 모델 추가
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Story(models.Model):
    """24시간 후 자동 삭제되는 스토리"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    media_file = models.FileField(upload_to='stories/', max_length=500)
    media_type = models.CharField(max_length=10, choices=[
        ('image', 'Image'),
        ('video', 'Video'),
    ], default='image')
    caption = models.TextField(blank=True, null=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    # 스토리 설정
    is_highlight = models.BooleanField(default=False)  # 하이라이트 스토리
    highlight_title = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Story'
        verbose_name_plural = 'Stories'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # 24시간 후 만료
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def time_remaining(self):
        """남은 시간 (초)"""
        if self.is_expired:
            return 0
        delta = self.expires_at - timezone.now()
        return int(delta.total_seconds())
    
    def __str__(self):
        return f"{self.user.username}'s story - {self.created_at}"


class StoryView(models.Model):
    """스토리 조회 기록"""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_views')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['story', 'viewer']
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['story', 'viewer']),
            models.Index(fields=['-viewed_at']),
        ]
    
    def __str__(self):
        return f"{self.viewer.username} viewed {self.story.user.username}'s story"


class StoryReaction(models.Model):
    """스토리 반응 (DM으로 전송)"""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_reactions')
    emoji = models.CharField(max_length=10, blank=True, null=True)
    message = models.TextField(blank=True, null=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['story', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} reacted to {self.story.user.username}'s story"
