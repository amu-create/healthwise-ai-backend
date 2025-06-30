from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class WorkoutResult(models.Model):
    """운동 분석 결과"""
    EXERCISE_TYPES = (
        ('strength', '근력 운동'),
        ('cardio', '유산소 운동'),
        ('flexibility', '유연성 운동'),
        ('balance', '균형 운동'),
        ('general', '일반 운동'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_results')
    exercise_name = models.CharField(max_length=100, verbose_name='운동 이름')
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPES, default='general')
    
    # 운동 데이터
    duration = models.IntegerField(help_text='운동 시간 (초)', validators=[MinValueValidator(1)])
    rep_count = models.IntegerField(default=0, help_text='반복 횟수')
    average_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='평균 자세 점수 (0-100)'
    )
    total_frames = models.IntegerField(default=0, help_text='분석된 프레임 수')
    calories_burned = models.FloatField(default=0, help_text='소모 칼로리')
    
    # 피드백 및 분석
    key_feedback = models.JSONField(default=list, help_text='주요 피드백 목록')
    muscle_groups = models.JSONField(default=list, help_text='타겟 근육 그룹')
    angle_scores = models.JSONField(default=dict, blank=True, help_text='관절별 평균 점수')
    
    # 미디어 (선택사항)
    video_url = models.URLField(blank=True, null=True)
    thumbnail_url = models.URLField(blank=True, null=True)
    
    # 메타 정보
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workout_results'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['exercise_name', '-created_at']),
        ]
        verbose_name = '운동 결과'
        verbose_name_plural = '운동 결과'
    
    def __str__(self):
        return f"{self.user.username} - {self.exercise_name} ({self.created_at.strftime('%Y-%m-%d')})"
    
    @property
    def grade(self):
        """점수에 따른 등급 반환"""
        if self.average_score >= 90:
            return 'A+'
        elif self.average_score >= 80:
            return 'A'
        elif self.average_score >= 70:
            return 'B'
        elif self.average_score >= 60:
            return 'C'
        else:
            return 'D'
    
    def get_duration_display(self):
        """운동 시간을 읽기 쉬운 형식으로 반환"""
        minutes = self.duration // 60
        seconds = self.duration % 60
        if minutes > 0:
            return f"{minutes}분 {seconds}초"
        return f"{seconds}초"


class WorkoutGoal(models.Model):
    """운동 목표"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_goals')
    exercise_name = models.CharField(max_length=100, verbose_name='운동 이름')
    
    # 목표 설정
    target_duration = models.IntegerField(null=True, blank=True, help_text='목표 운동 시간 (초)')
    target_reps = models.IntegerField(null=True, blank=True, help_text='목표 반복 횟수')
    target_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='목표 자세 점수'
    )
    target_calories = models.FloatField(null=True, blank=True, help_text='목표 칼로리')
    
    # 목표 기간
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    
    # 상태
    is_active = models.BooleanField(default=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workout_goals'
        unique_together = [['user', 'exercise_name', 'is_active']]
        verbose_name = '운동 목표'
        verbose_name_plural = '운동 목표'
    
    def __str__(self):
        return f"{self.user.username} - {self.exercise_name} 목표"
    
    def check_completion(self, workout_result):
        """운동 결과가 목표를 달성했는지 확인"""
        if not self.is_active:
            return False
        
        completed = True
        
        if self.target_duration and workout_result.duration < self.target_duration:
            completed = False
        if self.target_reps and workout_result.rep_count < self.target_reps:
            completed = False
        if self.target_score and workout_result.average_score < self.target_score:
            completed = False
        if self.target_calories and workout_result.calories_burned < self.target_calories:
            completed = False
        
        if completed and not self.completed_at:
            self.completed_at = timezone.now()
            self.save()
        
        return completed
