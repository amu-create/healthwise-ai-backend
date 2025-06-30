from rest_framework import serializers
from .models import WorkoutAchievement, UserWorkoutAchievement, UserWorkoutLevel, UserGoal
from django.contrib.auth import get_user_model

User = get_user_model()


class WorkoutAchievementSerializer(serializers.ModelSerializer):
    """업적 정보 시리얼라이저"""
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    badge_level_display = serializers.CharField(source='get_badge_level_display', read_only=True)
    
    class Meta:
        model = WorkoutAchievement
        fields = [
            'id', 'name', 'name_en', 'name_es', 
            'description', 'description_en', 'description_es',
            'category', 'category_display',
            'badge_level', 'badge_level_display',
            'icon_name', 'target_value', 'points', 'is_active'
        ]
    
    def get_name(self, obj):
        """사용자 언어에 따른 이름 반환"""
        language = self.context.get('language', 'ko')
        return obj.get_name(language)
    
    def get_description(self, obj):
        """사용자 언어에 따른 설명 반환"""
        language = self.context.get('language', 'ko')
        return obj.get_description(language)


class UserWorkoutAchievementSerializer(serializers.ModelSerializer):
    """사용자 업적 진행 상황 시리얼라이저"""
    achievement = WorkoutAchievementSerializer(read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = UserWorkoutAchievement
        fields = [
            'id', 'achievement', 'progress', 'progress_percentage',
            'completed', 'completed_at', 'created_at', 'updated_at'
        ]


class UserWorkoutLevelSerializer(serializers.ModelSerializer):
    """사용자 레벨 정보 시리얼라이저"""
    required_exp_for_next_level = serializers.ReadOnlyField()
    current_level_progress = serializers.ReadOnlyField()
    main_achievements = UserWorkoutAchievementSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserWorkoutLevel
        fields = [
            'id', 'username', 'level', 'experience_points',
            'total_achievement_points', 'main_achievements',
            'required_exp_for_next_level', 'current_level_progress',
            'created_at', 'updated_at'
        ]


class UserGoalSerializer(serializers.ModelSerializer):
    """사용자 목표 시리얼라이저"""
    progress_percentage = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    goal_type_display = serializers.CharField(source='get_goal_type_display', read_only=True)
    
    class Meta:
        model = UserGoal
        fields = [
            'id', 'goal_type', 'goal_type_display',
            'target_value', 'current_value',
            'progress_percentage', 'is_completed',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['progress_percentage', 'is_completed']


class AchievementProgressSerializer(serializers.Serializer):
    """업적 진행률 요약 시리얼라이저 (대시보드용)"""
    total_achievements = serializers.IntegerField()
    completed_achievements = serializers.IntegerField()
    total_points = serializers.IntegerField()
    completion_percentage = serializers.FloatField()
    recent_achievements = UserWorkoutAchievementSerializer(many=True)
    active_goals = UserGoalSerializer(many=True)
    user_level = UserWorkoutLevelSerializer()
