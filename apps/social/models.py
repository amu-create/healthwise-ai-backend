from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class SocialProfile(models.Model):
    """사용자 프로필 - 소셜 기능을 위한 확장 프로필"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='social_profile_obj')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    followers = models.ManyToManyField(User, related_name='social_following', blank=True)
    
    # 프라이버시 설정
    is_private = models.BooleanField(default=False)
    show_achievement_badges = models.BooleanField(default=True)
    show_workout_stats = models.BooleanField(default=True)
    
    # 통계
    total_posts = models.IntegerField(default=0)
    total_workouts = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_user_profile'
    
    def __str__(self):
        return f"{self.user.username}'s profile"


class SocialPost(models.Model):
    """운동 기록 게시물"""
    VISIBILITY_CHOICES = [
        ('public', '전체 공개'),
        ('followers', '팔로워만'),
        ('private', '나만 보기'),
    ]
    
    MEDIA_TYPE_CHOICES = [
        ('image', '이미지'),
        ('video', '동영상'),
        ('gif', 'GIF'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_posts')
    content = models.TextField()
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    
    # 운동 정보
    workout_log = models.ForeignKey('api.WorkoutRoutineLog', on_delete=models.SET_NULL, null=True, blank=True)
    workout_result = models.ForeignKey('workout.WorkoutResult', on_delete=models.SET_NULL, null=True, blank=True)
    exercise_name = models.CharField(max_length=100, blank=True)
    duration = models.IntegerField(null=True, blank=True, help_text="운동 시간(분)")
    calories_burned = models.IntegerField(null=True, blank=True)
    
    # 태그
    tags = models.JSONField(default=list, blank=True)
    
    # 미디어
    media_file = models.FileField(upload_to='social/posts/%Y/%m/', blank=True, null=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, blank=True, null=True)
    media_url = models.URLField(blank=True, null=True, help_text="외부 미디어 URL (YouTube, GIF 등)")
    
    # 상호작용
    likes = models.ManyToManyField(User, related_name='social_liked_posts', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_workout_post'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


# Post 모델을 SocialPost의 별칭으로 추가
Post = SocialPost

class SocialComment(models.Model):
    """댓글"""
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_comment'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}"


class SocialFriendRequest(models.Model):
    """친구 요청"""
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('accepted', '수락됨'),
        ('rejected', '거절됨'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_sent_friend_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_received_friend_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'social_friend_request'
        unique_together = ('from_user', 'to_user')
    
    def __str__(self):
        return f"{self.from_user.username} → {self.to_user.username} ({self.status})"


class SocialNotification(models.Model):
    """알림"""
    NOTIFICATION_TYPES = [
        ('like', '좋아요'),
        ('comment', '댓글'),
        ('follow', '팔로우'),
        ('friend_request', '친구 요청'),
        ('achievement', '업적 달성'),
        ('workout_reminder', '운동 알림'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # 관련 객체
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, null=True, blank=True)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='social_sent_notifications')
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_notification'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.type}: {self.title}"


class SavedPost(models.Model):
    """저장된 게시물"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_saved_post'
        unique_together = ['user', 'post']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.post.id}"


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
        db_table = 'social_story'
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
        db_table = 'social_story_view'
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
        db_table = 'social_story_reaction'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['story', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} reacted to {self.story.user.username}'s story"


class Conversation(models.Model):
    """1:1 대화 (DM)"""
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_conversation'
        ordering = ['-updated_at']
    
    def get_other_participant(self, user):
        """현재 사용자가 아닌 다른 참가자 반환"""
        return self.participants.exclude(id=user.id).first()
    
    def get_last_message(self):
        """마지막 메시지 반환"""
        return self.messages.first()
    
    def get_unread_count(self, user):
        """읽지 않은 메시지 수"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()
    
    def __str__(self):
        participants = self.participants.all()
        if participants.count() == 2:
            return f"Conversation between {participants[0].username} and {participants[1].username}"
        return f"Conversation {self.id}"


class DirectMessage(models.Model):
    """다이렉트 메시지"""
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    content = models.TextField(max_length=1000)
    
    # 미디어 지원
    media_file = models.FileField(
        upload_to='dm/media/%Y/%m/', 
        blank=True, 
        null=True,
        max_length=500
    )
    media_type = models.CharField(
        max_length=10, 
        choices=[
            ('image', 'Image'),
            ('video', 'Video'),
            ('audio', 'Audio'),
            ('file', 'File'),
        ], 
        blank=True, 
        null=True
    )
    
    # 메시지 상태
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 메시지 타입 (일반, 스토리 반응, 게시물 공유 등)
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text Message'),
            ('story_reaction', 'Story Reaction'),
            ('post_share', 'Post Share'),
            ('media', 'Media'),
        ],
        default='text'
    )
    
    # 참조 객체 (스토리 반응, 게시물 공유 시)
    referenced_story = models.ForeignKey(
        Story, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='dm_references'
    )
    referenced_post = models.ForeignKey(
        SocialPost, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='dm_shares'
    )
    
    class Meta:
        db_table = 'social_direct_message'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['is_read', 'conversation']),
        ]
    
    def mark_as_read(self):
        """메시지를 읽음으로 표시"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


class MessageReaction(models.Model):
    """메시지 반응 (이모지)"""
    message = models.ForeignKey(
        DirectMessage, 
        on_delete=models.CASCADE, 
        related_name='reactions'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='message_reactions'
    )
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_message_reaction'
        unique_together = ['message', 'user', 'emoji']
    
    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message {self.message.id}"
