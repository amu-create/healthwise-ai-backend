from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, FoodAnalysis, DailyNutrition, Exercise, WorkoutRoutine,
    RoutineExercise, WorkoutSession, NutritionEntry, SocialPost,
    PostLike, PostComment, HealthConsultation, WorkoutLog,
    ChatSession, ChatMessage
)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'birth_date', 'gender', 'height', 'weight', 'diseases',
            'health_conditions', 'allergies', 'medications', 'fitness_level',
            'fitness_goals', 'workout_days_per_week', 'weekly_workout_goal',
            'daily_steps_goal', 'preferred_exercises', 'preferred_foods'
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['id']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'profile']
    
    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # 프로필 생성
        UserProfile.objects.create(user=user, **profile_data)
        
        return user


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'


class RoutineExerciseSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    exercise_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = RoutineExercise
        fields = ['id', 'exercise', 'exercise_id', 'sets', 'reps', 'duration', 'rest_time', 'order']


class WorkoutRoutineSerializer(serializers.ModelSerializer):
    exercises = RoutineExerciseSerializer(source='routineexercise_set', many=True, read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = WorkoutRoutine
        fields = ['id', 'user', 'name', 'description', 'exercises', 
                 'total_duration', 'difficulty', 'is_public', 'created_at', 'updated_at']


class WorkoutSessionSerializer(serializers.ModelSerializer):
    routine = WorkoutRoutineSerializer(read_only=True)
    routine_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = WorkoutSession
        fields = ['id', 'routine', 'routine_id', 'date', 'duration', 
                 'calories_burned', 'notes', 'completed']


class NutritionEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = NutritionEntry
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class PostCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PostComment
        fields = ['id', 'user', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class SocialPostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    workout_session = WorkoutSessionSerializer(read_only=True)
    comments = PostCommentSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = SocialPost
        fields = ['id', 'user', 'content', 'workout_session', 'image_url', 
                 'likes_count', 'comments_count', 'comments', 'is_liked', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'likes_count', 'comments_count', 
                          'created_at', 'updated_at']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class HealthConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthConsultation
        fields = '__all__'
        read_only_fields = ['user', 'ai_response', 'created_at']


class FoodAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodAnalysis
        fields = [
            'id', 'food_name', 'description', 'image_url', 'calories',
            'protein', 'carbohydrates', 'fat', 'fiber', 'sugar', 'sodium',
            'analysis_summary', 'recommendations', 'analyzed_at'
        ]
        read_only_fields = ['id', 'analyzed_at']


class FoodAnalysisRequestSerializer(serializers.Serializer):
    food_name = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    image_base64 = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        if not attrs.get('food_name') and not attrs.get('image_base64'):
            raise serializers.ValidationError("음식 이름 또는 이미지 중 하나는 필수입니다.")
        return attrs


class DailyNutritionSerializer(serializers.ModelSerializer):
    food_analyses = FoodAnalysisSerializer(many=True, read_only=True)
    
    class Meta:
        model = DailyNutrition
        fields = [
            'id', 'date', 'total_calories', 'total_protein',
            'total_carbohydrates', 'total_fat', 'food_analyses',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkoutLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = WorkoutLog
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'message', 'context', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'user_session_number', 'started_at', 'ended_at', 
                 'is_active', 'summary', 'messages', 'message_count']
        read_only_fields = ['id', 'user_session_number', 'started_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()
