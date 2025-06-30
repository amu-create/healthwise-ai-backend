from rest_framework import serializers
from .models import Exercise, AnalysisSession, AnalysisFrame, UserExerciseStats


class ExerciseSerializer(serializers.ModelSerializer):
    """운동 시리얼라이저"""
    class Meta:
        model = Exercise
        fields = '__all__'


class AnalysisFrameSerializer(serializers.ModelSerializer):
    """프레임 분석 시리얼라이저"""
    class Meta:
        model = AnalysisFrame
        fields = '__all__'


class AnalysisSessionSerializer(serializers.ModelSerializer):
    """분석 세션 시리얼라이저"""
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    exercise_category = serializers.CharField(source='exercise.category', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True, required=False)
    frames = AnalysisFrameSerializer(many=True, read_only=True)
    
    class Meta:
        model = AnalysisSession
        fields = '__all__'
        read_only_fields = ['average_score', 'max_score', 'min_score', 'total_frames', 'feedback_summary']


class AnalysisSessionCreateSerializer(serializers.ModelSerializer):
    """분석 세션 생성 시리얼라이저"""
    
    class Meta:
        model = AnalysisSession
        fields = ['exercise', 'mode', 'video_file']
        extra_kwargs = {
            'video_file': {'required': False}
        }
    
    def validate(self, attrs):
        """mode에 따른 validation"""
        mode = attrs.get('mode')
        video_file = attrs.get('video_file')
        
        if mode == 'upload' and not video_file:
            raise serializers.ValidationError({
                'video_file': '업로드 모드에서는 비디오 파일이 필요합니다.'
            })
        
        return attrs


class UserExerciseStatsSerializer(serializers.ModelSerializer):
    """사용자 운동 통계 시리얼라이저"""
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    exercise_category = serializers.CharField(source='exercise.category', read_only=True)
    
    class Meta:
        model = UserExerciseStats
        fields = '__all__'
        read_only_fields = ['user', 'total_sessions', 'total_reps', 'total_duration', 
                          'best_score', 'average_score', 'last_session_date', 'improvement_rate']


class PoseAnalysisRequestSerializer(serializers.Serializer):
    """실시간 포즈 분석 요청 시리얼라이저"""
    session_id = serializers.IntegerField()
    landmarks = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )
    timestamp = serializers.FloatField()
    frame_index = serializers.IntegerField()


class VideoAnalysisSerializer(serializers.Serializer):
    """비디오 업로드 분석 시리얼라이저"""
    video = serializers.FileField()
    exercise_id = serializers.IntegerField()
    
    def validate_video(self, value):
        """비디오 파일 검증"""
        valid_extensions = ['.mp4', '.avi', '.mov', '.webm', '.ogg']
        file_extension = value.name.lower().split('.')[-1]
        
        if f'.{file_extension}' not in valid_extensions:
            raise serializers.ValidationError(
                f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(valid_extensions)}"
            )
        
        # 파일 크기 제한 (100MB)
        if value.size > 100 * 1024 * 1024:
            raise serializers.ValidationError("파일 크기는 100MB를 초과할 수 없습니다.")
        
        return value
