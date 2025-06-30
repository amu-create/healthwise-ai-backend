# api/models_social.py
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point

User = get_user_model()

class WorkoutPartner(models.Model):
    """운동 파트너 매칭 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partner_profile')
    location = gis_models.PointField(geography=True, null=True, blank=True)
    preferred_time = models.CharField(max_length=50)  # morning, afternoon, evening, night
    workout_types = models.JSONField(default=list)  # ['weight', 'cardio', 'yoga', 'pilates']
    fitness_level = models.CharField(max_length=20)  # beginner, intermediate, advanced
    bio = models.TextField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    last_active = models.DateTimeField(auto_now=True)
    
    # 매칭 설정
    max_distance_km = models.IntegerField(default=5)
    preferred_gender = models.CharField(max_length=10, default='any')  # male, female, any
    age_range_min = models.IntegerField(default=18)
    age_range_max = models.IntegerField(default=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['location', 'is_active']),
            models.Index(fields=['workout_types', 'fitness_level']),
        ]

class PartnerMatch(models.Model):
    """매칭된 파트너 관계"""
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('accepted', '수락됨'),
        ('rejected', '거절됨'),
        ('blocked', '차단됨'),
    ]
    
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_matches')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_matches')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    match_score = models.FloatField(default=0.0)  # 매칭 점수 (0-100)
    distance_km = models.FloatField(null=True, blank=True)
    
    # 매칭 이유
    match_reasons = models.JSONField(default=list)  # ['같은 운동 선호', '비슷한 레벨', '가까운 거리']
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['requester', 'receiver']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

class WorkoutSession(models.Model):
    """함께하는 운동 세션"""
    partners = models.ManyToManyField(User, related_name='partner_sessions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    workout_type = models.CharField(max_length=50)
    location_name = models.CharField(max_length=200)
    location_address = models.CharField(max_length=500)
    location_point = gis_models.PointField(geography=True, null=True, blank=True)
    
    scheduled_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    max_participants = models.IntegerField(default=2)
    
    is_public = models.BooleanField(default=False)  # 공개 세션 여부
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['scheduled_date']

class Challenge(models.Model):
    """커뮤니티 챌린지"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    image_url = models.URLField(blank=True)
    
    challenge_type = models.CharField(max_length=50)  # daily, weekly, monthly
    category = models.CharField(max_length=50)  # weight_loss, muscle_gain, endurance
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    # 목표 설정
    target_type = models.CharField(max_length=50)  # workouts, calories, distance
    target_value = models.IntegerField()
    target_unit = models.CharField(max_length=20)  # times, kcal, km
    
    # 보상
    points_reward = models.IntegerField(default=100)
    badge_name = models.CharField(max_length=100, blank=True)
    badge_icon = models.CharField(max_length=50, blank=True)
    
    participants = models.ManyToManyField(User, through='ChallengeParticipation', related_name='challenges')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']

class ChallengeParticipation(models.Model):
    """챌린지 참여 기록"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    
    current_progress = models.FloatField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # 일일 진행 기록
    daily_progress = models.JSONField(default=dict)  # {'2025-01-13': 10, '2025-01-14': 15}
    
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'challenge']

class UserAchievement(models.Model):
    """사용자 업적/뱃지"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=50)  # badge, milestone, streak
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    icon = models.CharField(max_length=50)
    
    # 달성 조건
    criteria_type = models.CharField(max_length=50)  # workouts, days, challenges
    criteria_value = models.IntegerField()
    
    earned_at = models.DateTimeField(auto_now_add=True)
    points_earned = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'achievement_type', 'name']
        ordering = ['-earned_at']
