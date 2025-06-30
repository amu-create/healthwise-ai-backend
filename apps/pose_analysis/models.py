from django.db import models
from django.conf import settings
from django.utils import timezone
import json

class Exercise(models.Model):
    """운동 정의 모델"""
    DIFFICULTY_CHOICES = [
        ('beginner', '초급'),
        ('intermediate', '중급'),
        ('advanced', '고급'),
    ]
    
    CATEGORY_CHOICES = [
        ('upper', '상체'),
        ('lower', '하체'),
        ('core', '코어'),
        ('fullbody', '전신'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='운동명')
    name_en = models.CharField(max_length=100, verbose_name='영문명')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name='카테고리')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, verbose_name='난이도')
    description = models.TextField(verbose_name='설명')
    target_muscles = models.JSONField(default=list, verbose_name='타겟 근육')
    angle_calculations = models.JSONField(default=dict, verbose_name='각도 계산 설정')
    key_points = models.JSONField(default=list, verbose_name='핵심 포인트')
    icon = models.CharField(max_length=10, default='💪', verbose_name='아이콘')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '운동'
        verbose_name_plural = '운동 목록'
        ordering = ['category', 'difficulty', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class AnalysisSession(models.Model):
    """운동 분석 세션"""
    MODE_CHOICES = [
        ('realtime', '실시간'),
        ('upload', '업로드'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name='사용자')
    guest_id = models.CharField(max_length=100, null=True, blank=True, verbose_name='게스트 ID')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, verbose_name='운동')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, verbose_name='분석 모드')
    duration = models.FloatField(default=0, verbose_name='운동 시간(초)')
    rep_count = models.IntegerField(default=0, verbose_name='반복 횟수')
    average_score = models.FloatField(default=0, verbose_name='평균 점수')
    max_score = models.FloatField(default=0, verbose_name='최고 점수')
    min_score = models.FloatField(default=0, verbose_name='최저 점수')
    total_frames = models.IntegerField(default=0, verbose_name='총 프레임 수')
    feedback_summary = models.JSONField(default=dict, verbose_name='피드백 요약')
    video_file = models.FileField(upload_to='pose_analysis/videos/', null=True, blank=True, verbose_name='비디오 파일')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='생성일시')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='완료일시')
    
    class Meta:
        verbose_name = '분석 세션'
        verbose_name_plural = '분석 세션 목록'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.exercise.name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def calculate_statistics(self, frames):
        """프레임 데이터로부터 통계 계산"""
        if not frames:
            return
        
        scores = [frame.overall_score for frame in frames]
        self.average_score = sum(scores) / len(scores)
        self.max_score = max(scores)
        self.min_score = min(scores)
        self.total_frames = len(frames)
        
        # 피드백 요약 생성
        feedback_counts = {}
        for frame in frames:
            if frame.feedback:
                feedback_data = json.loads(frame.feedback) if isinstance(frame.feedback, str) else frame.feedback
                for feedback in feedback_data:
                    feedback_counts[feedback] = feedback_counts.get(feedback, 0) + 1
        
        # 가장 빈번한 피드백 정렬
        sorted_feedback = sorted(feedback_counts.items(), key=lambda x: x[1], reverse=True)
        self.feedback_summary = {
            'most_common': sorted_feedback[:5],
            'total_feedback_count': sum(feedback_counts.values())
        }
        
        self.save()


class AnalysisFrame(models.Model):
    """개별 프레임 분석 데이터"""
    session = models.ForeignKey(AnalysisSession, on_delete=models.CASCADE, related_name='frames', verbose_name='세션')
    timestamp = models.FloatField(verbose_name='타임스탬프(초)')
    frame_index = models.IntegerField(verbose_name='프레임 인덱스')
    angles = models.JSONField(verbose_name='관절 각도')
    scores = models.JSONField(verbose_name='부위별 점수')
    overall_score = models.FloatField(verbose_name='전체 점수')
    feedback = models.JSONField(default=list, verbose_name='피드백')
    corrections = models.JSONField(default=list, verbose_name='교정 사항')
    is_in_position = models.BooleanField(default=False, verbose_name='올바른 자세')
    rep_phase = models.CharField(max_length=20, null=True, blank=True, verbose_name='운동 단계')
    
    class Meta:
        verbose_name = '프레임 분석'
        verbose_name_plural = '프레임 분석 목록'
        ordering = ['session', 'frame_index']
    
    def __str__(self):
        return f"Frame {self.frame_index} - Score: {self.overall_score:.1f}"


class UserExerciseStats(models.Model):
    """사용자별 운동 통계"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='사용자')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, verbose_name='운동')
    total_sessions = models.IntegerField(default=0, verbose_name='총 세션 수')
    total_reps = models.IntegerField(default=0, verbose_name='총 반복 횟수')
    total_duration = models.FloatField(default=0, verbose_name='총 운동 시간(초)')
    best_score = models.FloatField(default=0, verbose_name='최고 점수')
    average_score = models.FloatField(default=0, verbose_name='평균 점수')
    last_session_date = models.DateTimeField(null=True, blank=True, verbose_name='마지막 운동일')
    improvement_rate = models.FloatField(default=0, verbose_name='향상률(%)')
    
    class Meta:
        verbose_name = '사용자 운동 통계'
        verbose_name_plural = '사용자 운동 통계'
        unique_together = ['user', 'exercise']
        ordering = ['user', 'exercise']
    
    def __str__(self):
        return f"{self.user.username} - {self.exercise.name}"
    
    def update_stats(self, session):
        """새 세션으로 통계 업데이트"""
        self.total_sessions += 1
        self.total_reps += session.rep_count
        self.total_duration += session.duration
        
        if session.average_score > self.best_score:
            self.best_score = session.average_score
        
        # 평균 점수 재계산
        sessions = AnalysisSession.objects.filter(
            user=self.user,
            exercise=self.exercise
        ).aggregate(
            avg_score=models.Avg('average_score')
        )
        self.average_score = sessions['avg_score'] or 0
        
        self.last_session_date = session.created_at
        
        # 향상률 계산 (최근 5개 세션 vs 이전 5개 세션)
        recent_sessions = AnalysisSession.objects.filter(
            user=self.user,
            exercise=self.exercise
        ).order_by('-created_at')[:5]
        
        if recent_sessions.count() >= 5:
            recent_avg = sum(s.average_score for s in recent_sessions) / 5
            
            older_sessions = AnalysisSession.objects.filter(
                user=self.user,
                exercise=self.exercise
            ).order_by('-created_at')[5:10]
            
            if older_sessions.count() >= 5:
                older_avg = sum(s.average_score for s in older_sessions) / 5
                if older_avg > 0:
                    self.improvement_rate = ((recent_avg - older_avg) / older_avg) * 100
        
        self.save()
