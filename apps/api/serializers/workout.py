from rest_framework import serializers
from ..models import (
    Exercise, Routine, RoutineExercise, FitnessProfile,
    WorkoutRoutineLog, FoodAnalysis, DailyNutrition
)


class ExerciseSerializer(serializers.ModelSerializer):
    """운동 시리얼라이저"""
    class Meta:
        model = Exercise
        fields = '__all__'


class RoutineExerciseSerializer(serializers.ModelSerializer):
    """루틴 운동 시리얼라이저"""
    exercise = ExerciseSerializer(read_only=True)
    exercise_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = RoutineExercise
        fields = ['id', 'exercise', 'exercise_id', 'order', 'sets', 'reps', 'notes']


class RoutineSerializer(serializers.ModelSerializer):
    """루틴 시리얼라이저"""
    exercises = RoutineExerciseSerializer(source='routineexercise_set', many=True, read_only=True)
    
    class Meta:
        model = Routine
        fields = ['id', 'name', 'level', 'exercises', 'created_at', 'is_ai_generated']
        read_only_fields = ['created_at', 'is_ai_generated']


class FitnessProfileSerializer(serializers.ModelSerializer):
    """피트니스 프로필 시리얼라이저"""
    class Meta:
        model = FitnessProfile
        fields = [
            'experience', 'goal', 'frequency', 'duration',
            'weight', 'height', 'body_fat', 'muscle_mass',
            'gender', 'birth_date', 'injuries'
        ]


class WorkoutRoutineLogSerializer(serializers.ModelSerializer):
    """운동 루틴 기록 시리얼라이저"""
    routine = RoutineSerializer(read_only=True)
    routine_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = WorkoutRoutineLog
        fields = [
            'id', 'routine', 'routine_id', 'date',
            'duration', 'notes', 'created_at'
        ]
        read_only_fields = ['created_at']


class AIWorkoutRequestSerializer(serializers.Serializer):
    """AI 운동 추천 요청 시리얼라이저"""
    muscle_group = serializers.CharField()
    level = serializers.ChoiceField(choices=['초급', '중급', '상급'])
    duration = serializers.IntegerField(min_value=15, max_value=120)
    equipment_available = serializers.BooleanField(default=True)
    specific_goals = serializers.CharField(required=False, allow_blank=True)


class FoodAnalysisSerializer(serializers.ModelSerializer):
    """음식 분석 시리얼라이저"""
    class Meta:
        model = FoodAnalysis
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class FoodAnalysisRequestSerializer(serializers.Serializer):
    """음식 분석 요청 시리얼라이저"""
    image = serializers.ImageField(required=False)
    text = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if not data.get('image') and not data.get('text'):
            raise serializers.ValidationError("이미지 또는 텍스트 중 하나는 반드시 필요합니다.")
        return data


class DailyNutritionSerializer(serializers.ModelSerializer):
    """일일 영양 시리얼라이저"""
    food_analyses = FoodAnalysisSerializer(many=True, read_only=True)
    
    class Meta:
        model = DailyNutrition
        fields = '__all__'
        read_only_fields = ['user', 'date']
