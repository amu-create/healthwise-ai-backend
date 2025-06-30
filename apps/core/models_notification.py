from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class NotificationSettings(models.Model):
    """
    사용자별 알림 설정을 관리하는 모델
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notification_settings'
    )
    
    # FCM 토큰
    fcm_token = models.TextField(blank=True, null=True)
    fcm_token_updated_at = models.DateTimeField(auto_now=True)
    
    # 알림 활성화 설정
    enable_workout_reminders = models.BooleanField(default=True)
    enable_goal_achievement_notif = models.BooleanField(default=True)
    enable_social_activity_notif = models.BooleanField(default=True)
    enable_weekly_summary = models.BooleanField(default=True)
    
    # 알림 시간 설정
    reminder_time = models.TimeField(
        default='09:00',
        help_text='운동 알림을 받을 시간'
    )
    
    # 알림 빈도 설정
    reminder_days = models.CharField(
        max_length=20,
        default='1,2,3,4,5',  # 월-금
        help_text='알림을 받을 요일 (0=일요일, 6=토요일)'
    )
    
    # 조용한 시간 설정
    quiet_hours_start = models.TimeField(
        default='22:00',
        help_text='알림을 받지 않을 시간 시작'
    )
    quiet_hours_end = models.TimeField(
        default='07:00',
        help_text='알림을 받지 않을 시간 종료'
    )
    
    # 언어 설정
    notification_language = models.CharField(
        max_length=10,
        default='ko',
        choices=[
            ('ko', '한국어'),
            ('en', 'English'),
        ]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '알림 설정'
        verbose_name_plural = '알림 설정'
        
    def __str__(self):
        return f"{self.user.username}의 알림 설정"
    
    def get_reminder_days_list(self):
        """알림 요일을 리스트로 반환"""
        if not self.reminder_days:
            return []
        return [int(day) for day in self.reminder_days.split(',')]
    
    def set_reminder_days_list(self, days_list):
        """알림 요일을 리스트로 설정"""
        self.reminder_days = ','.join(str(day) for day in days_list)


class NotificationLog(models.Model):
    """
    발송된 알림 기록을 저장하는 모델
    """
    NOTIFICATION_TYPES = [
        ('workout_reminder', '운동 알림'),
        ('goal_achievement', '목표 달성'),
        ('social_activity', '친구 활동'),
        ('weekly_summary', '주간 요약'),
    ]
    
    STATUS_CHOICES = [
        ('sent', '전송됨'),
        ('failed', '전송 실패'),
        ('pending', '대기중'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_logs'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True)
    
    # FCM 응답 정보
    fcm_message_id = models.CharField(max_length=100, blank=True, null=True)
    fcm_response = models.JSONField(blank=True, null=True)
    
    # 추가 데이터
    data = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = '알림 기록'
        verbose_name_plural = '알림 기록'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()} - {self.created_at}"
