from rest_framework import serializers
from django.contrib.auth.models import User
from .models import FitnessProfile, WorkoutRecord, MusicPreference, WorkoutMusic


class FitnessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class WorkoutRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutRecord
        fields = '__all__'
        read_only_fields = ['user', 'date']


class MusicPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MusicPreference
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class WorkoutMusicSerializer(serializers.ModelSerializer):
    music_preference = MusicPreferenceSerializer(read_only=True)
    
    class Meta:
        model = WorkoutMusic
        fields = '__all__'


class UserProfileSerializer(serializers.ModelSerializer):
    fitness_profile = FitnessProfileSerializer(read_only=True)
    recent_workouts = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'fitness_profile', 'recent_workouts']
    
    def get_recent_workouts(self, obj):
        recent = obj.workout_records.all()[:5]
        return WorkoutRecordSerializer(recent, many=True).data
