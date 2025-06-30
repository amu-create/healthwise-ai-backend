from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, UserProfile, WorkoutCategory, WorkoutVideo,
    WorkoutLog, DietLog, ChatMessage, ExerciseLocation,
    MusicRecommendation
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'is_staff', 'is_active', 'created_at']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'username']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('추가 정보', {'fields': ('created_at', 'updated_at')}),
    )
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'height', 'weight', 'exercise_experience']
    list_filter = ['gender', 'exercise_experience']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(WorkoutCategory)
class WorkoutCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(WorkoutVideo)
class WorkoutVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty', 'duration', 'view_count']
    list_filter = ['category', 'difficulty']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'view_count', 'like_count']

@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'workout_name', 'duration', 'calories_burned']
    list_filter = ['date']
    search_fields = ['user__email', 'workout_name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(DietLog)
class DietLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'meal_type', 'total_calories']
    list_filter = ['meal_type', 'date']
    search_fields = ['user__email']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'sender', 'created_at']
    list_filter = ['sender', 'created_at']
    search_fields = ['user__email', 'message']
    readonly_fields = ['created_at']

@admin.register(ExerciseLocation)
class ExerciseLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'location_type', 'address', 'rating']
    list_filter = ['location_type', 'rating']
    search_fields = ['name', 'address']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(MusicRecommendation)
class MusicRecommendationAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'workout_type', 'bpm', 'energy_level']
    list_filter = ['workout_type', 'energy_level']
    search_fields = ['title', 'artist', 'album']
    readonly_fields = ['created_at']
