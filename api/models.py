from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Supabase 연동
    supabase_id = models.UUIDField(null=True, blank=True, unique=True, db_index=True, help_text="Supabase user ID")
    
    # 기본 정보
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], null=True, blank=True)
    height = models.FloatField(null=True, blank=True, help_text="Height in cm", validators=[MinValueValidator(50), MaxValueValidator(300)])
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg", validators=[MinValueValidator(20), MaxValueValidator(500)])
    
    # 건강 정보
    diseases = models.JSONField(default=list, blank=True, help_text="List of diseases")
    health_conditions = models.JSONField(default=list, blank=True, help_text="List of health conditions")
    allergies = models.JSONField(default=list, blank=True, help_text="List of allergies")
    medications = models.JSONField(default=list, blank=True, help_text="List of current medications")
    
    # 피트니스 정보
    fitness_level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ], default='beginner')
    fitness_goals = models.JSONField(default=list, blank=True)
    
    # 운동 목표 (원본 프로젝트 참고)
    workout_days_per_week = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(7)])
    weekly_workout_goal = models.IntegerField(default=3, help_text='주간 운동 목표 횟수')
    daily_steps_goal = models.IntegerField(default=10000, help_text='일일 목표 걸음 수')
    
    # 선호도 정보 
    preferred_exercises = models.JSONField(default=list, help_text='선호하는 운동 목록')
    preferred_foods = models.JSONField(default=list, help_text='선호하는 음식 목록')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Exercise(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)  # cardio, strength, flexibility, etc.
    description = models.TextField()
    instructions = models.TextField()
    duration = models.IntegerField(help_text="Duration in minutes")
    calories_per_minute = models.FloatField(default=5.0)
    difficulty = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ])
    equipment_needed = models.JSONField(default=list, blank=True)
    muscle_groups = models.JSONField(default=list, blank=True)
    youtube_url = models.URLField(null=True, blank=True)
    thumbnail_url = models.URLField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

class WorkoutRoutine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routines')
    name = models.CharField(max_length=200)
    description = models.TextField()
    exercises = models.ManyToManyField(Exercise, through='RoutineExercise')
    total_duration = models.IntegerField(help_text="Total duration in minutes")
    difficulty = models.CharField(max_length=20)
    is_public = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class RoutineExercise(models.Model):
    routine = models.ForeignKey(WorkoutRoutine, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.IntegerField(default=1)
    reps = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True, help_text="Duration in seconds")
    rest_time = models.IntegerField(default=30, help_text="Rest time in seconds")
    order = models.IntegerField(default=0)

class WorkoutSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_sessions')
    routine = models.ForeignKey(WorkoutRoutine, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField(help_text="Actual duration in minutes")
    calories_burned = models.FloatField()
    notes = models.TextField(blank=True)
    completed = models.BooleanField(default=True)

class NutritionEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nutrition_entries')
    date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=[
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack')
    ])
    food_name = models.CharField(max_length=200)
    quantity = models.FloatField()
    unit = models.CharField(max_length=50)
    calories = models.FloatField()
    protein = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    fiber = models.FloatField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

class SocialPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    workout_session = models.ForeignKey(WorkoutSession, on_delete=models.SET_NULL, null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')

class PostComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class HealthConsultation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultations')
    question = models.TextField()
    ai_response = models.TextField()
    category = models.CharField(max_length=100)  # nutrition, exercise, health, etc.
    is_public = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)


# 영양 분석 관련 모델
class FoodAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_analyses')
    food_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    image_base64 = models.TextField(blank=True, null=True)
    calories = models.IntegerField()
    protein = models.FloatField(help_text="단백질 (g)")
    carbohydrates = models.FloatField(help_text="탄수화물 (g)")
    fat = models.FloatField(help_text="지방 (g)")
    fiber = models.FloatField(null=True, blank=True, help_text="식이섬유 (g)")
    sugar = models.FloatField(null=True, blank=True, help_text="당류 (g)")
    sodium = models.FloatField(null=True, blank=True, help_text="나트륨 (mg)")
    analysis_summary = models.TextField()
    recommendations = models.TextField()
    analyzed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "음식 분석"
        verbose_name_plural = "음식 분석 목록"
        ordering = ['-analyzed_at']


# 일일 영양 기록
class DailyNutrition(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_nutrition')
    date = models.DateField()
    total_calories = models.IntegerField(default=0)
    total_protein = models.FloatField(default=0)
    total_carbohydrates = models.FloatField(default=0)
    total_fat = models.FloatField(default=0)
    food_analyses = models.ManyToManyField(FoodAnalysis)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "일일 영양 기록"
        verbose_name_plural = "일일 영양 기록 목록"
        unique_together = [['user', 'date']]
        ordering = ['-date']

# WorkoutLog 모델 추가 (원본 프로젝트 참고)
class WorkoutLog(models.Model):
    """운동 기록"""
    WORKOUT_TYPE_CHOICES = [
        ('running', '러닝'),
        ('cycling', '자전거'),
        ('swimming', '수영'),
        ('gym', '헬스장'),
        ('yoga', '요가'),
        ('pilates', '필라테스'),
        ('hiking', '등산'),
        ('sports', '스포츠'),
        ('home', '홈트레이닝'),
        ('other', '기타'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_logs')
    date = models.DateField()
    duration = models.IntegerField(help_text='분 단위')
    calories_burned = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # 운동 세부 정보
    workout_name = models.CharField(max_length=100)
    workout_type = models.CharField(max_length=20, choices=WORKOUT_TYPE_CHOICES, default='other')
    sets = models.IntegerField(null=True, blank=True)
    reps = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True, help_text='kg 단위')
    
    # 지도 관련 정보
    start_latitude = models.FloatField(null=True, blank=True)
    start_longitude = models.FloatField(null=True, blank=True)
    end_latitude = models.FloatField(null=True, blank=True)
    end_longitude = models.FloatField(null=True, blank=True)
    route_coordinates = models.JSONField(default=list, help_text='경로 좌표 목록')
    distance = models.FloatField(null=True, blank=True, help_text='이동 거리 (km)')
    
    # 운동 중 측정값
    avg_heart_rate = models.IntegerField(null=True, blank=True, help_text='평균 심박수')
    max_heart_rate = models.IntegerField(null=True, blank=True, help_text='최대 심박수')
    steps = models.IntegerField(null=True, blank=True, help_text='걸음 수')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '운동 기록'
        verbose_name_plural = '운동 기록들'
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.workout_name}"

# ChatSession 모델 추가 (챗봇 세션 관리)
class ChatSession(models.Model):
    """챗봇 대화 세션"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    user_session_number = models.IntegerField(default=1, help_text='사용자별 세션 번호')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # 세션 요약 정보
    summary = models.TextField(blank=True, help_text='세션 대화 요약')
    extracted_preferences = models.JSONField(default=dict, help_text='추출된 선호도 정보')
    
    class Meta:
        verbose_name = '챗봇 세션'
        verbose_name_plural = '챗봇 세션들'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.email} - 세션 #{self.user_session_number} ({self.started_at})"

# ChatMessage 모델 추가
class ChatMessage(models.Model):
    """챗봇 대화 메시지"""
    SENDER_CHOICES = [
        ('user', '사용자'),
        ('bot', '챗봇'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField()
    
    # 메타데이터
    context = models.JSONField(null=True, blank=True, help_text='대화 컨텍스트')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = '챗봇 메시지'
        verbose_name_plural = '챗봇 메시지들'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.sender} - {self.created_at}"
