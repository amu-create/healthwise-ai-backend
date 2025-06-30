from django.contrib import admin
from .models import (
    Exercise, Routine, RoutineExercise, FitnessProfile, 
    WorkoutRoutineLog, FoodAnalysis, DailyNutrition,
    UserProfile, Follow, FriendRequest, WorkoutPost, PostLike, PostComment
)

# 운동 관리
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'muscle_group', 'exercise_type', 'default_sets', 'default_reps']
    list_filter = ['exercise_type', 'muscle_group']
    search_fields = ['name', 'muscle_group']
    ordering = ['name']


# 루틴 운동 인라인
class RoutineExerciseInline(admin.TabularInline):
    model = RoutineExercise
    extra = 1
    ordering = ['order']


# 루틴 관리
@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'user', 'is_ai_generated', 'created_at']
    list_filter = ['level', 'is_ai_generated']
    search_fields = ['name', 'user__username']
    inlines = [RoutineExerciseInline]
    date_hierarchy = 'created_at'


# 피트니스 프로필 관리
@admin.register(FitnessProfile)
class FitnessProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'experience', 'goal', 'frequency', 'created_at']
    list_filter = ['experience', 'goal', 'gender']
    search_fields = ['user__username', 'user__email']
    date_hierarchy = 'created_at'


# 운동 루틴 기록 관리
@admin.register(WorkoutRoutineLog)
class WorkoutRoutineLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'routine', 'date', 'duration', 'created_at']
    list_filter = ['date']
    search_fields = ['user__username', 'routine__name']
    date_hierarchy = 'date'


# 음식 분석 관리
@admin.register(FoodAnalysis)
class FoodAnalysisAdmin(admin.ModelAdmin):
    list_display = ['user', 'food_name', 'calories', 'protein', 'carbohydrates', 'fat', 'analyzed_at']
    list_filter = ['analyzed_at']
    search_fields = ['user__username', 'food_name']
    date_hierarchy = 'analyzed_at'
    readonly_fields = ['analyzed_at']


# 일일 영양 기록 관리
@admin.register(DailyNutrition)
class DailyNutritionAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'total_calories', 'total_protein', 'total_carbohydrates', 'total_fat']
    list_filter = ['date']
    search_fields = ['user__username']
    date_hierarchy = 'date'
    filter_horizontal = ['food_analyses']


# 소셜 기능 관리
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'privacy_setting', 'created_at']
    list_filter = ['privacy_setting', 'allow_friend_requests']
    search_fields = ['user__username', 'bio']
    date_hierarchy = 'created_at'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    search_fields = ['follower__username', 'following__username']
    date_hierarchy = 'created_at'


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['from_user__username', 'to_user__username']
    date_hierarchy = 'created_at'


@admin.register(WorkoutPost)
class WorkoutPostAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_preview', 'visibility', 'likes_count', 'comments_count', 'created_at']
    list_filter = ['visibility', 'media_type', 'created_at']
    search_fields = ['user__username', 'content']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    search_fields = ['user__username', 'post__content']
    date_hierarchy = 'created_at'


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'content_preview', 'created_at']
    search_fields = ['user__username', 'content']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
