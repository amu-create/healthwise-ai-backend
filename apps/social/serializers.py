from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    SocialProfile, SocialPost, SocialComment, SocialFriendRequest, 
    SocialNotification, SavedPost, Story, StoryView, StoryReaction,
    Conversation, DirectMessage, MessageReaction
)
from django.utils import timezone

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """기본 사용자 시리얼라이저"""
    profile_picture_url = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_picture_url', 'profile', 'is_following']
        read_only_fields = ['id']
    
    def get_profile_picture_url(self, obj):
        try:
            profile = obj.profile
            if profile and profile.profile_image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(profile.profile_image.url)
        except:
            pass
        # social_profile_obj 체크
        try:
            social_profile = obj.social_profile_obj
            if social_profile and social_profile.profile_picture:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(social_profile.profile_picture.url)
        except:
            pass
        return None
    
    def get_profile(self, obj):
        try:
            profile = obj.profile
            if profile:
                return {
                    'profile_image': profile.profile_image.url if profile.profile_image else None
                }
        except:
            pass
        return None
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user != obj:
            try:
                # 해당 사용자의 소셜 프로필을 팔로우하고 있는지 확인
                social_profile = SocialProfile.objects.filter(user=obj).first()
                if social_profile:
                    return social_profile.followers.filter(id=request.user.id).exists()
            except:
                pass
        return False


class SocialProfileSerializer(serializers.ModelSerializer):
    """사용자 프로필 시리얼라이저"""
    user = UserSerializer(read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = SocialProfile
        fields = [
            'id', 'user', 'bio', 'profile_picture',
            'followers_count', 'following_count', 'is_following',
            'is_private', 'show_achievement_badges', 'show_workout_stats',
            'total_posts', 'total_workouts',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'followers_count', 'following_count', 'is_following', 'created_at', 'updated_at']
    
    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_following_count(self, obj):
        # 현재 사용자가 팔로우하는 프로필 수
        return SocialProfile.objects.filter(followers=obj.user).count()
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.followers.filter(id=request.user.id).exists()
        return False


class SocialCommentSerializer(serializers.ModelSerializer):
    """댓글 시리얼라이저"""
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    post = serializers.PrimaryKeyRelatedField(
        queryset=SocialPost.objects.all(),
        write_only=True
    )
    
    class Meta:
        model = SocialComment
        fields = ['id', 'user', 'post', 'content', 'parent', 'replies', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.replies.all()
            return SocialCommentSerializer(replies, many=True, context=self.context).data
        return []


class SocialPostSerializer(serializers.ModelSerializer):
    """운동 게시물 시리얼라이저"""
    user = UserSerializer(read_only=True)
    workout_info = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comments = SocialCommentSerializer(many=True, read_only=True)
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)
    media_type_display = serializers.CharField(source='get_media_type_display', read_only=True)
    can_edit = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    
    class Meta:
        model = SocialPost
        fields = [
            'id', 'user', 'content', 'visibility', 'visibility_display',
            'workout_log', 'workout_info', 'exercise_name', 'duration', 'calories_burned',
            'media_file', 'media_type', 'media_type_display', 'media_url',
            'likes_count', 'comments_count', 'is_liked', 'is_saved', 'comments', 'can_edit',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'media_type']
    
    def get_workout_info(self, obj):
        if obj.workout_log:
            try:
                from apps.api.serializers.workout import WorkoutRoutineLogSerializer
                return WorkoutRoutineLogSerializer(obj.workout_log, context=self.context).data
            except:
                return None
        return None
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedPost.objects.filter(user=request.user, post=obj).exists()
        return False
    
    def validate_media_file(self, value):
        if value:
            # 파일 크기 제한 (10MB for images/GIF, 50MB for videos)
            if value.size > 50 * 1024 * 1024:  # 50MB
                raise serializers.ValidationError("파일 크기는 50MB를 초과할 수 없습니다.")
            
            # 파일 형식 확인
            content_type = getattr(value, 'content_type', '')
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'video/webm']
            if content_type not in allowed_types:
                raise serializers.ValidationError("지원하지 않는 파일 형식입니다.")
        
        return value


class SocialFriendRequestSerializer(serializers.ModelSerializer):
    """친구 요청 시리얼라이저"""
    from_user = UserSerializer(read_only=True)
    to_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )
    to_user_data = UserSerializer(source='to_user', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SocialFriendRequest
        fields = [
            'id', 'from_user', 'to_user', 'to_user_data', 'status', 'status_display',
            'message', 'created_at', 'responded_at'
        ]
        read_only_fields = ['id', 'from_user', 'created_at', 'responded_at']


class SocialNotificationSerializer(serializers.ModelSerializer):
    """알림 시리얼라이저"""
    from_user = UserSerializer(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = SocialNotification
        fields = [
            'id', 'type', 'type_display', 'title', 'message',
            'post', 'from_user', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StoryViewSerializer(serializers.ModelSerializer):
    """스토리 조회 기록 시리얼라이저"""
    viewer = UserSerializer(read_only=True)
    
    class Meta:
        model = StoryView
        fields = ['id', 'viewer', 'viewed_at']
        read_only_fields = ['id', 'viewed_at']


class StoryReactionSerializer(serializers.ModelSerializer):
    """스토리 반응 시리얼라이저"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StoryReaction
        fields = ['id', 'user', 'emoji', 'message', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class StorySerializer(serializers.ModelSerializer):
    """스토리 시리얼라이저"""
    user = UserSerializer(read_only=True)
    views_count = serializers.SerializerMethodField()
    reactions_count = serializers.SerializerMethodField()
    has_viewed = serializers.SerializerMethodField()
    time_remaining = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    viewers = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = [
            'id', 'user', 'media_file', 'media_type', 'caption',
            'created_at', 'expires_at', 'is_highlight', 'highlight_title',
            'views_count', 'reactions_count', 'has_viewed',
            'time_remaining', 'is_expired', 'viewers'
        ]
        read_only_fields = ['id', 'created_at', 'expires_at']
    
    def get_views_count(self, obj):
        return obj.views.count()
    
    def get_reactions_count(self, obj):
        return obj.reactions.count()
    
    def get_has_viewed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.views.filter(viewer=request.user).exists()
        return False
    
    def get_viewers(self, obj):
        # 스토리 작성자만 조회자 목록을 볼 수 있음
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj.user == request.user:
            views = obj.views.all().select_related('viewer')
            return StoryViewSerializer(views, many=True, context=self.context).data
        return []
    
    def validate_media_file(self, value):
        if value:
            # 파일 크기 제한 (10MB for images, 50MB for videos)
            if value.size > 50 * 1024 * 1024:  # 50MB
                raise serializers.ValidationError("파일 크기는 50MB를 초과할 수 없습니다.")
            
            # 파일 형식 확인 - content_type이 없을 수도 있으므로 안전하게 처리
            content_type = getattr(value, 'content_type', '')
            
            # content_type이 없으면 파일 확장자로 판단
            if not content_type and hasattr(value, 'name'):
                file_ext = value.name.lower().split('.')[-1]
                ext_to_type = {
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'png': 'image/png',
                    'gif': 'image/gif',
                    'mp4': 'video/mp4',
                    'webm': 'video/webm'
                }
                content_type = ext_to_type.get(file_ext, '')
            
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'video/webm']
            if content_type and content_type not in allowed_types:
                raise serializers.ValidationError("지원하지 않는 파일 형식입니다.")
            
            # 비디오 길이 제한 (15초) - 실제 구현에서는 ffmpeg 등을 사용
            if content_type and content_type.startswith('video'):
                pass
        
        return value
    
    def create(self, validated_data):
        # media_type이 설정되어 있는지 확인
        if 'media_file' in validated_data and 'media_type' not in validated_data:
            media_file = validated_data['media_file']
            content_type = getattr(media_file, 'content_type', '')
            
            # content_type이 없으면 파일 확장자로 판단
            if not content_type and hasattr(media_file, 'name'):
                file_ext = media_file.name.lower().split('.')[-1]
                if file_ext == 'gif':
                    validated_data['media_type'] = 'gif'
                elif file_ext in ['jpg', 'jpeg', 'png']:
                    validated_data['media_type'] = 'image'
                elif file_ext in ['mp4', 'webm', 'mov']:
                    validated_data['media_type'] = 'video'
                else:
                    validated_data['media_type'] = 'image'  # 기본값
            else:
                # content_type으로 판단
                if content_type == 'image/gif':
                    validated_data['media_type'] = 'gif'
                elif content_type.startswith('image'):
                    validated_data['media_type'] = 'image'
                elif content_type.startswith('video'):
                    validated_data['media_type'] = 'video'
                else:
                    validated_data['media_type'] = 'image'  # 기본값
        
        return super().create(validated_data)


class UserStoriesSerializer(serializers.ModelSerializer):
    """사용자별 스토리 목록 시리얼라이저"""
    user = UserSerializer(read_only=True)
    stories = serializers.SerializerMethodField()
    has_unviewed = serializers.SerializerMethodField()
    latest_story_time = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['user', 'stories', 'has_unviewed', 'latest_story_time']
    
    def get_stories(self, obj):
        # 만료되지 않은 스토리만 반환
        active_stories = obj.stories.filter(
            expires_at__gt=timezone.now()
        ).order_by('-created_at')
        return StorySerializer(active_stories, many=True, context=self.context).data
    
    def get_has_unviewed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # 사용자의 활성 스토리 중 내가 보지 않은 것이 있는지 확인
            active_stories = obj.stories.filter(expires_at__gt=timezone.now())
            for story in active_stories:
                if not story.views.filter(viewer=request.user).exists():
                    return True
        return False
    
    def get_latest_story_time(self, obj):
        latest_story = obj.stories.filter(
            expires_at__gt=timezone.now()
        ).order_by('-created_at').first()
        return latest_story.created_at if latest_story else None


class MessageReactionSerializer(serializers.ModelSerializer):
    """메시지 반응 시리얼라이저"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ['id', 'user', 'emoji', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class DirectMessageSerializer(serializers.ModelSerializer):
    """다이렉트 메시지 시리얼라이저"""
    sender = UserSerializer(read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    referenced_story = StorySerializer(read_only=True)
    referenced_post = SocialPostSerializer(read_only=True)
    
    class Meta:
        model = DirectMessage
        fields = [
            'id', 'conversation', 'sender', 'content',
            'media_file', 'media_type', 'is_read', 'read_at',
            'message_type', 'referenced_story', 'referenced_post',
            'reactions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sender', 'created_at', 'updated_at']
        extra_kwargs = {
            'conversation': {'write_only': True}
        }
    
    def validate_media_file(self, value):
        if value:
            # 파일 크기 제한 (이미지/비디오: 50MB, 기타: 10MB)
            max_size = 50 * 1024 * 1024  # 50MB
            if value.size > max_size:
                raise serializers.ValidationError("파일 크기는 50MB를 초과할 수 없습니다.")
            
            # 파일 형식 확인
            content_type = getattr(value, 'content_type', '')
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 
                'video/mp4', 'video/webm',
                'audio/mpeg', 'audio/wav',
                'application/pdf', 'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            
            # 미디어 타입 자동 설정
            if content_type.startswith('image'):
                self.initial_data['media_type'] = 'image'
            elif content_type.startswith('video'):
                self.initial_data['media_type'] = 'video'
            elif content_type.startswith('audio'):
                self.initial_data['media_type'] = 'audio'
            else:
                self.initial_data['media_type'] = 'file'
        
        return value


class ConversationSerializer(serializers.ModelSerializer):
    """대화 시리얼라이저"""
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'participants', 'last_message', 
            'unread_count', 'other_participant',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        last_message = obj.get_last_message()
        if last_message:
            return DirectMessageSerializer(last_message, context=self.context).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0
    
    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            other = obj.get_other_participant(request.user)
            if other:
                return UserSerializer(other, context=self.context).data
        return None


class CreateConversationSerializer(serializers.Serializer):
    """대화 생성 시리얼라이저"""
    participant_id = serializers.IntegerField()
    
    def validate_participant_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("사용자를 찾을 수 없습니다.")
        return value


class SendMessageSerializer(serializers.ModelSerializer):
    """메시지 전송 시리얼라이저"""
    class Meta:
        model = DirectMessage
        fields = ['content', 'media_file', 'message_type', 'referenced_story', 'referenced_post']
        
    def validate(self, data):
        # 메시지 타입에 따른 검증
        if data.get('message_type') == 'story_reaction' and not data.get('referenced_story'):
            raise serializers.ValidationError("스토리 반응은 스토리를 참조해야 합니다.")
        
        if data.get('message_type') == 'post_share' and not data.get('referenced_post'):
            raise serializers.ValidationError("게시물 공유는 게시물을 참조해야 합니다.")
        
        # 내용이나 미디어 중 하나는 있어야 함
        if not data.get('content') and not data.get('media_file'):
            raise serializers.ValidationError("메시지 내용이나 미디어 파일 중 하나는 필수입니다.")
        
        return data
