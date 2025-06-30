# Base serializers
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.core.models import UserProfile

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile', 'profile_picture_url']
        
    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'age': profile.age,
                'height': profile.height,
                'weight': profile.weight,
                'gender': profile.gender,
                'exercise_experience': profile.exercise_experience,
                'diseases': profile.diseases or [],
                'allergies': profile.allergies or []
            }
        except:
            return None
            
    def get_profile_picture_url(self, obj):
        try:
            if hasattr(obj, 'profile') and obj.profile.profile_picture:
                request = self.context.get('request')
                if request and obj.profile.profile_picture:
                    return request.build_absolute_uri(obj.profile.profile_picture.url)
        except:
            pass
        return None

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm']
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        return attrs
        
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        # 프로필 자동 생성
        UserProfile.objects.create(user=user)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("새 비밀번호가 일치하지 않습니다.")
        return attrs

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['age', 'height', 'weight', 'gender', 'exercise_experience', 'diseases', 'allergies']

class HealthOptionsSerializer(serializers.Serializer):
    diseases = serializers.ListField(child=serializers.CharField())
    allergies = serializers.ListField(child=serializers.CharField())
