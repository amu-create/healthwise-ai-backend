from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 기본 정보
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], null=True, blank=True)
    height = models.FloatField(null=True, blank=True, help_text="Height in cm")
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    
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
