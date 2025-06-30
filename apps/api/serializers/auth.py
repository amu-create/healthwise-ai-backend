from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.core.models import UserProfile
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """사용자 프로필 시리얼라이저"""
    profile_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'age', 'height', 'weight', 'gender', 
            'exercise_experience', 'diseases', 'allergies',
            'profile_image', 'profile_image_url'
        ]
        read_only_fields = ['profile_image_url']
    
    def get_profile_image_url(self, obj):
        if obj.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
        return None


class UserSerializer(serializers.ModelSerializer):
    """사용자 정보 시리얼라이저"""
    profile = ProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'profile', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    """회원가입 시리얼라이저"""
    password2 = serializers.CharField(write_only=True, required=True)
    age = serializers.IntegerField(write_only=True)
    height = serializers.IntegerField(write_only=True)
    weight = serializers.IntegerField(write_only=True)
    gender = serializers.ChoiceField(choices=['M', 'F', 'O'], write_only=True)
    exercise_experience = serializers.ChoiceField(
        choices=['beginner', 'intermediate', 'advanced', 'expert'],
        write_only=True
    )
    diseases = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        write_only=True
    )
    allergies = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        write_only=True
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password2',
            'age', 'height', 'weight', 'gender', 
            'exercise_experience', 'diseases', 'allergies'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        
        # 비밀번호 유효성 검사
        validate_password(attrs['password'])
        
        return attrs
    
    def create(self, validated_data):
        # 프로필 관련 데이터 추출
        profile_data = {
            'age': validated_data.pop('age'),
            'height': validated_data.pop('height'),
            'weight': validated_data.pop('weight'),
            'gender': validated_data.pop('gender'),
            'exercise_experience': validated_data.pop('exercise_experience'),
            'diseases': validated_data.pop('diseases', []),
            'allergies': validated_data.pop('allergies', []),
        }
        
        # password2 제거
        validated_data.pop('password2')
        
        # 사용자 생성
        user = User.objects.create_user(**validated_data)
        
        # 프로필 생성
        UserProfile.objects.create(user=user, **profile_data)
        
        return user


class LoginSerializer(serializers.Serializer):
    """로그인 시리얼라이저"""
    email = serializers.EmailField()
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    """비밀번호 변경 시리얼라이저"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError("새 비밀번호가 일치하지 않습니다.")
        
        # 새 비밀번호 유효성 검사
        validate_password(attrs['new_password'])
        
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """프로필 업데이트 시리얼라이저"""
    class Meta:
        model = UserProfile
        fields = [
            'age', 'height', 'weight', 'gender',
            'exercise_experience', 'diseases', 'allergies'
        ]


class HealthOptionsSerializer(serializers.Serializer):
    """건강 옵션 시리얼라이저"""
    diseases = serializers.ListField(child=serializers.CharField())
    allergies = serializers.ListField(child=serializers.CharField())
