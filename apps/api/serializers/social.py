from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import (
    UserProfile, Follow, FriendRequest,
    WorkoutPost, PostLike, PostComment
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_picture_url']
    
    def get_profile_picture_url(self, obj):
        try:
            # social_profile 관계 확인 (UserProfile 모델)
            if hasattr(obj, 'social_profile') and obj.social_profile.profile_picture_url:
                return obj.social_profile.profile_picture_url
            # userprofile 관계 확인 (다른 프로필 모델)
            if hasattr(obj, 'userprofile') and hasattr(obj.userprofile, 'profile_picture') and obj.userprofile.profile_picture:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.userprofile.profile_picture.url)
        except:
            pass
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    is_friend = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'bio', 'profile_picture_url',
            'privacy_setting', 'show_achievement_badges', 'show_workout_stats',
            'followers_count', 'following_count',
            'is_following', 'is_friend'
        ]
    
    def get_followers_count(self, obj):
        return obj.user.followers.count()
    
    def get_following_count(self, obj):
        return obj.user.following.count()
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                follower=request.user,
                following=obj.user
            ).exists()
        return False
    
    def get_is_friend(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # 양방향 팔로우 확인
            return (
                Follow.objects.filter(
                    follower=request.user,
                    following=obj.user
                ).exists() and
                Follow.objects.filter(
                    follower=obj.user,
                    following=request.user
                ).exists()
            )
        return False


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PostComment
        fields = ['id', 'user', 'content', 'created_at']
        read_only_fields = ['created_at']


class WorkoutPostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    media_url = serializers.SerializerMethodField()
    visibility_display = serializers.SerializerMethodField()
    workout_info = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkoutPost
        fields = [
            'id', 'user', 'content', 'workout_log', 'workout_info',
            'media_file', 'media_type', 'media_url', 'image_url',
            'visibility', 'visibility_display', 'created_at', 'updated_at',
            'likes_count', 'comments_count', 'is_liked',
            'comments'
        ]
        read_only_fields = ['created_at', 'updated_at', 'media_type']
    
    def get_media_url(self, obj):
        if obj.media_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.media_file.url)
        return obj.media_url
    
    def get_visibility_display(self, obj):
        return obj.get_visibility_display()
    
    def get_workout_info(self, obj):
        if obj.workout_log:
            return {
                'date': obj.workout_log.date.isoformat(),
                'duration': obj.workout_log.duration,
                'routine_name': obj.workout_log.routine.name if obj.workout_log.routine else None
            }
        return None
    
    def create(self, validated_data):
        media_file = validated_data.get('media_file')
        if media_file:
            # 파일 타입 자동 설정
            content_type = media_file.content_type
            if content_type.startswith('image/'):
                if content_type == 'image/gif':
                    validated_data['media_type'] = 'gif'
                else:
                    validated_data['media_type'] = 'image'
            elif content_type.startswith('video/'):
                validated_data['media_type'] = 'video'
        
        return super().create(validated_data)


class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    to_user_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = FriendRequest
        fields = [
            'id', 'from_user', 'to_user', 'to_user_id',
            'status', 'created_at'
        ]
        read_only_fields = ['from_user', 'status', 'created_at']
