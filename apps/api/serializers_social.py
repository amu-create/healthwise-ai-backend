from rest_framework import serializers
from .models import (
    UserProfile, Follow, FriendRequest, WorkoutPost, 
    PostLike, PostComment, WorkoutRoutineLog
)
from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()


class UserSocialSerializer(serializers.ModelSerializer):
    """소셜 기능용 사용자 기본 정보"""
    profile_picture_url = serializers.CharField(source='social_profile.profile_picture_url', read_only=True)
    bio = serializers.CharField(source='social_profile.bio', read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture_url', 'bio', 
                 'followers_count', 'following_count', 'is_following']
    
    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_following_count(self, obj):
        return obj.following.count()
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                follower=request.user,
                following=obj
            ).exists()
        return False


class UserProfileSerializer(serializers.ModelSerializer):
    """사용자 소셜 프로필"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'email', 'bio', 'profile_picture_url',
            'privacy_setting', 'allow_friend_requests',
            'show_achievement_badges', 'show_workout_stats', 'show_nutrition_stats',
            'followers_count', 'following_count', 'posts_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_followers_count(self, obj):
        return obj.user.followers.count()
    
    def get_following_count(self, obj):
        return obj.user.following.count()
    
    def get_posts_count(self, obj):
        return obj.user.workout_posts.count()


class FollowSerializer(serializers.ModelSerializer):
    """팔로우 관계"""
    follower = UserSocialSerializer(read_only=True)
    following = UserSocialSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']


class FriendRequestSerializer(serializers.ModelSerializer):
    """친구 요청"""
    from_user = UserSocialSerializer(read_only=True)
    to_user = UserSocialSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = FriendRequest
        fields = [
            'id', 'from_user', 'to_user', 'message',
            'status', 'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']


class CommentSerializer(serializers.ModelSerializer):
    """댓글"""
    user = UserSocialSerializer(read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PostComment
        fields = [
            'id', 'user', 'content', 'parent',
            'replies_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_replies_count(self, obj):
        return obj.replies.count()


class WorkoutPostSerializer(serializers.ModelSerializer):
    """운동 게시물"""
    user = UserSocialSerializer(read_only=True)
    workout_info = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)
    
    class Meta:
        model = WorkoutPost
        fields = [
            'id', 'user', 'workout_log', 'workout_info',
            'content', 'image_url', 'visibility', 'visibility_display',
            'likes_count', 'comments_count', 'is_liked',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['likes_count', 'comments_count', 'created_at', 'updated_at']
    
    def get_workout_info(self, obj):
        if obj.workout_log:
            return {
                'date': obj.workout_log.date,
                'duration': obj.workout_log.duration,
                'routine_name': obj.workout_log.routine.name if obj.workout_log.routine else None
            }
        return None
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(
                user=request.user,
                post=obj
            ).exists()
        return False


class WorkoutPostDetailSerializer(WorkoutPostSerializer):
    """운동 게시물 상세 (댓글 포함)"""
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta(WorkoutPostSerializer.Meta):
        fields = WorkoutPostSerializer.Meta.fields + ['comments']


class PostLikeSerializer(serializers.ModelSerializer):
    """좋아요"""
    user = UserSocialSerializer(read_only=True)
    
    class Meta:
        model = PostLike
        fields = ['id', 'user', 'created_at']
