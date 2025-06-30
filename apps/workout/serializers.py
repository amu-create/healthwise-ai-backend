from rest_framework import serializers
from .models import WorkoutResult, WorkoutGoal
from apps.social.models import Post
from apps.achievements.services import check_workout_achievements


class WorkoutResultSerializer(serializers.ModelSerializer):
    """운동 결과 시리얼라이저"""
    user = serializers.ReadOnlyField(source='user.username')
    grade = serializers.ReadOnlyField()
    duration_display = serializers.ReadOnlyField(source='get_duration_display')
    
    class Meta:
        model = WorkoutResult
        fields = [
            'id', 'user', 'exercise_name', 'exercise_type',
            'duration', 'duration_display', 'rep_count', 
            'average_score', 'grade', 'total_frames',
            'calories_burned', 'key_feedback', 'muscle_groups',
            'angle_scores', 'video_url', 'thumbnail_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # 현재 사용자 설정
        validated_data['user'] = self.context['request'].user
        workout_result = super().create(validated_data)
        
        # 업적 체크 (비동기로 처리하거나 별도 태스크로)
        try:
            check_workout_achievements(workout_result.user, workout_result)
        except Exception as e:
            # 업적 체크 실패시에도 운동 결과는 저장되도록
            print(f"Achievement check failed: {e}")
        
        return workout_result


class WorkoutGoalSerializer(serializers.ModelSerializer):
    """운동 목표 시리얼라이저"""
    user = serializers.ReadOnlyField(source='user.username')
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkoutGoal
        fields = [
            'id', 'user', 'exercise_name',
            'target_duration', 'target_reps', 'target_score', 'target_calories',
            'start_date', 'end_date', 'is_active', 'completed_at',
            'progress', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'completed_at', 'created_at', 'updated_at']
    
    def get_progress(self, obj):
        """목표 대비 진행률 계산"""
        if not obj.is_active:
            return {'status': 'completed' if obj.completed_at else 'inactive'}
        
        # 최근 운동 결과로 진행률 계산
        recent_results = WorkoutResult.objects.filter(
            user=obj.user,
            exercise_name=obj.exercise_name,
            created_at__gte=obj.start_date
        ).order_by('-created_at')[:5]
        
        if not recent_results:
            return {'status': 'no_progress', 'percentage': 0}
        
        latest = recent_results[0]
        progress_data = {'status': 'in_progress'}
        
        # 각 목표별 진행률 계산
        if obj.target_duration:
            progress_data['duration_progress'] = min(100, (latest.duration / obj.target_duration) * 100)
        if obj.target_reps:
            progress_data['reps_progress'] = min(100, (latest.rep_count / obj.target_reps) * 100)
        if obj.target_score:
            progress_data['score_progress'] = min(100, (latest.average_score / obj.target_score) * 100)
        if obj.target_calories:
            progress_data['calories_progress'] = min(100, (latest.calories_burned / obj.target_calories) * 100)
        
        # 전체 진행률
        progress_values = [v for k, v in progress_data.items() if k.endswith('_progress')]
        if progress_values:
            progress_data['overall_progress'] = sum(progress_values) / len(progress_values)
        
        return progress_data


class ShareWorkoutResultSerializer(serializers.Serializer):
    """운동 결과 소셜 공유 시리얼라이저"""
    content = serializers.CharField(max_length=1000)
    workout_result_id = serializers.IntegerField()
    visibility = serializers.ChoiceField(
        choices=['public', 'friends', 'private'],
        default='public'
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list
    )
    
    def validate_workout_result_id(self, value):
        try:
            workout_result = WorkoutResult.objects.get(
                id=value, 
                user=self.context['request'].user
            )
        except WorkoutResult.DoesNotExist:
            raise serializers.ValidationError("운동 결과를 찾을 수 없습니다.")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        workout_result = WorkoutResult.objects.get(
            id=validated_data['workout_result_id'],
            user=user
        )
        
        # 소셜 포스트 생성
        post = Post.objects.create(
            author=user,
            content=validated_data['content'],
            visibility=validated_data['visibility'],
            workout_result=workout_result,
            tags=validated_data.get('tags', [])
        )
        
        return post
