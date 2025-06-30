from django.contrib import admin
from .models import Exercise, AnalysisSession, AnalysisFrame, UserExerciseStats


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'category', 'difficulty', 'is_active', 'created_at']
    list_filter = ['category', 'difficulty', 'is_active']
    search_fields = ['name', 'name_en', 'description']
    ordering = ['category', 'difficulty', 'name']


@admin.register(AnalysisSession)
class AnalysisSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'exercise', 'mode', 'average_score', 'duration', 'created_at', 'completed_at']
    list_filter = ['mode', 'exercise__category', 'created_at']
    search_fields = ['user__username', 'exercise__name']
    date_hierarchy = 'created_at'
    readonly_fields = ['average_score', 'max_score', 'min_score', 'total_frames', 'feedback_summary']


@admin.register(AnalysisFrame)
class AnalysisFrameAdmin(admin.ModelAdmin):
    list_display = ['session', 'frame_index', 'timestamp', 'overall_score', 'is_in_position']
    list_filter = ['is_in_position', 'session__exercise']
    search_fields = ['session__user__username']
    ordering = ['session', 'frame_index']


@admin.register(UserExerciseStats)
class UserExerciseStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'exercise', 'total_sessions', 'average_score', 'improvement_rate', 'last_session_date']
    list_filter = ['exercise__category', 'last_session_date']
    search_fields = ['user__username', 'exercise__name']
    readonly_fields = ['total_sessions', 'total_reps', 'total_duration', 'best_score', 
                      'average_score', 'last_session_date', 'improvement_rate']
