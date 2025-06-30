from django.contrib import admin
from .models import WorkoutResult, WorkoutGoal


@admin.register(WorkoutResult)
class WorkoutResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'exercise_name', 'average_score', 'grade', 'duration', 'created_at']
    list_filter = ['exercise_type', 'created_at', 'average_score']
    search_fields = ['user__username', 'exercise_name']
    readonly_fields = ['grade', 'get_duration_display', 'created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'exercise_name', 'exercise_type')
        }),
        ('운동 데이터', {
            'fields': ('duration', 'get_duration_display', 'rep_count', 'average_score', 'grade', 'total_frames', 'calories_burned')
        }),
        ('분석 정보', {
            'fields': ('key_feedback', 'muscle_groups', 'angle_scores')
        }),
        ('미디어', {
            'fields': ('video_url', 'thumbnail_url')
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(WorkoutGoal)
class WorkoutGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'exercise_name', 'is_active', 'start_date', 'completed_at']
    list_filter = ['is_active', 'start_date', 'completed_at']
    search_fields = ['user__username', 'exercise_name']
    readonly_fields = ['completed_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'exercise_name')
        }),
        ('목표 설정', {
            'fields': ('target_duration', 'target_reps', 'target_score', 'target_calories')
        }),
        ('기간', {
            'fields': ('start_date', 'end_date')
        }),
        ('상태', {
            'fields': ('is_active', 'completed_at')
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at')
        })
    )
