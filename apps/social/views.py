from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from .models import SocialProfile, SocialPost, SocialComment, SocialFriendRequest, SocialNotification, SavedPost, Story, StoryView, StoryReaction
from .serializers import (
    SocialProfileSerializer, SocialPostSerializer, SocialCommentSerializer,
    SocialFriendRequestSerializer, SocialNotificationSerializer,
    StorySerializer, StoryViewSerializer, StoryReactionSerializer, UserStoriesSerializer
)
from .websocket_utils import send_notification_to_user, send_achievement_to_user, send_level_up_to_user

User = get_user_model()


class SocialProfileViewSet(viewsets.ModelViewSet):
    """사용자 프로필 ViewSet"""
    queryset = SocialProfile.objects.all()
    serializer_class = SocialProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SocialProfile.objects.select_related('user').prefetch_related('followers')
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """사용자 팔로우"""
        profile = self.get_object()
        if profile.user == request.user:
            return Response({'error': '자기 자신을 팔로우할 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user in profile.followers.all():
            profile.followers.remove(request.user)
            # 알림 삭제
            SocialNotification.objects.filter(
                user=profile.user,
                from_user=request.user,
                type='follow'
            ).delete()
            return Response({'status': 'unfollowed'})
        else:
            profile.followers.add(request.user)
            # 알림 생성
            notification = SocialNotification.objects.create(
                user=profile.user,
                from_user=request.user,
                type='follow',
                title='새로운 팔로워',
                message=f'{request.user.username}님이 회원님을 팔로우했습니다.'
            )
            # WebSocket으로 실시간 알림 전송
            send_notification_to_user(profile.user.id, {
                'id': notification.id,
                'type': 'follow',
                'title': notification.title,
                'message': notification.message,
                'from_user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'avatar_url': request.user.profile_image.url if hasattr(request.user, 'profile_image') and request.user.profile_image else None
                },
                'created_at': notification.created_at.isoformat()
            })
            return Response({
                'status': 'followed',
                'followers_count': profile.followers.count(),
                'is_following': True
            })


class SocialPostViewSet(viewsets.ModelViewSet):
    """운동 게시물 ViewSet"""
    serializer_class = SocialPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = SocialPost.objects.select_related('user', 'workout_log').prefetch_related(
            'likes',
            Prefetch('comments', queryset=SocialComment.objects.select_related('user').order_by('created_at'))
        ).annotate(
            likes_count=Count('likes'),
            comments_count=Count('comments')
        )
        
        # 공개 게시물만 보이도록 필터링 (본인 게시물 제외)
        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(visibility='public') | Q(user=self.request.user)
            )
        else:
            queryset = queryset.filter(visibility='public')
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user)
        
        # 미디어 타입 자동 설정
        if post.media_file:
            content_type = post.media_file.file.content_type
            if content_type.startswith('image'):
                if content_type == 'image/gif':
                    post.media_type = 'gif'
                else:
                    post.media_type = 'image'
            elif content_type.startswith('video'):
                post.media_type = 'video'
            post.save()
        
        # 프로필 통계 업데이트
        profile, created = SocialProfile.objects.get_or_create(user=self.request.user)
        profile.total_posts += 1
        if post.workout_log:
            profile.total_workouts += 1
        profile.save()
    
    def perform_update(self, serializer):
        # 본인 게시물만 수정 가능
        if self.get_object().user != self.request.user:
            raise permissions.PermissionDenied("본인의 게시물만 수정할 수 있습니다.")
        serializer.save()
    
    def perform_destroy(self, instance):
        # 본인 게시물만 삭제 가능
        if instance.user != self.request.user:
            raise permissions.PermissionDenied("본인의 게시물만 삭제할 수 있습니다.")
        
        # 프로필 통계 업데이트
        try:
            profile = instance.user.social_profile_obj
            profile.total_posts -= 1
            if instance.workout_log:
                profile.total_workouts -= 1
            profile.save()
        except:
            pass
        
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """게시물 좋아요"""
        post = self.get_object()
        
        if request.user in post.likes.all():
            return Response({'error': '이미 좋아요를 누른 게시물입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        post.likes.add(request.user)
        
        # 알림 생성 (본인 제외)
        if post.user != request.user:
            notification = SocialNotification.objects.create(
                user=post.user,
                from_user=request.user,
                type='like',
                title='게시물 좋아요',
                message=f'{request.user.username}님이 회원님의 게시물을 좋아합니다.',
                post=post
            )
            # WebSocket으로 실시간 알림 전송
            send_notification_to_user(post.user.id, {
                'id': notification.id,
                'type': 'like',
                'title': notification.title,
                'message': notification.message,
                'from_user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'avatar_url': request.user.profile_image.url if hasattr(request.user, 'profile_image') and request.user.profile_image else None
                },
                'post_id': post.id,
                'created_at': notification.created_at.isoformat()
            })
        
        return Response({'status': 'liked', 'likes_count': post.likes.count()})
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """게시물 좋아요 취소"""
        post = self.get_object()
        
        if request.user not in post.likes.all():
            return Response({'error': '좋아요를 누르지 않은 게시물입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        post.likes.remove(request.user)
        
        # 알림 삭제
        SocialNotification.objects.filter(
            user=post.user,
            from_user=request.user,
            type='like',
            post=post
        ).delete()
        
        return Response({'status': 'unliked', 'likes_count': post.likes.count()})
    
    @action(detail=False, methods=['get'])
    def feed(self, request):
        """피드 조회 (전체/팔로잉/내 게시물)"""
        feed_type = request.query_params.get('feed_type', 'all')
        
        if feed_type == 'following' and request.user.is_authenticated:
            # 팔로잉한 사용자의 게시물만
            try:
                # 현재 사용자가 팔로우하는 사용자들을 찾기
                # 다른 사용자들의 프로필에서 현재 사용자가 팔로워로 있는 경우
                following_profiles = SocialProfile.objects.filter(
                    followers=request.user
                ).values_list('user', flat=True)
                queryset = self.get_queryset().filter(user__in=following_profiles)
            except:
                queryset = self.get_queryset().none()
        elif feed_type == 'my' and request.user.is_authenticated:
            # 내 게시물만
            queryset = self.get_queryset().filter(user=request.user)
        else:
            # 전체 공개 게시물
            queryset = self.get_queryset()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        """게시물 저장"""
        post = self.get_object()
        
        try:
            SavedPost.objects.create(user=request.user, post=post)
            return Response({'status': 'saved'})
        except IntegrityError:
            # 이미 저장된 경우
            return Response(
                {'error': '이미 저장된 게시물입니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def unsave(self, request, pk=None):
        """게시물 저장 취소"""
        post = self.get_object()
        
        try:
            saved = SavedPost.objects.get(user=request.user, post=post)
            saved.delete()
            return Response({'status': 'unsaved'})
        except SavedPost.DoesNotExist:
            return Response(
                {'error': '저장되지 않은 게시물입니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def saved(self, request):
        """저장된 게시물 목록"""
        saved_posts = SavedPost.objects.filter(
            user=request.user
        ).select_related('post')
        
        posts = [saved.post for saved in saved_posts]
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """인기 게시물 (24시간 내 좋아요 수 기준)"""
        from datetime import datetime, timedelta
        
        # 24시간 전
        yesterday = timezone.now() - timedelta(hours=24)
        
        # 인기 게시물: 최근 24시간 내 좋아요 수 + 댓글 수
        queryset = self.get_queryset().filter(
            created_at__gte=yesterday,
            visibility='public'
        ).annotate(
            score=Count('likes') * 2 + Count('comments')
        ).order_by('-score', '-created_at')[:20]
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """추천 게시물 (사용자 활동 기반)"""
        if not request.user.is_authenticated:
            # 비로그인 사용자에게는 인기 게시물 표시
            return self.popular(request)
        
        # 사용자가 좋아요한 게시물의 작성자들
        liked_users = User.objects.filter(
            social_posts__likes=request.user
        ).distinct()
        
        # 해당 사용자들의 최근 게시물
        queryset = self.get_queryset().filter(
            user__in=liked_users,
            visibility='public'
        ).exclude(
            user=request.user  # 본인 게시물 제외
        ).exclude(
            likes=request.user  # 이미 좋아요한 게시물 제외
        ).order_by('-created_at')[:20]
        
        # 추천할 게시물이 부족하면 인기 게시물 추가
        if queryset.count() < 10:
            popular_posts = self.get_queryset().filter(
                visibility='public'
            ).exclude(
                user=request.user
            ).exclude(
                likes=request.user
            ).annotate(
                likes_count=Count('likes')
            ).order_by('-likes_count', '-created_at')[:10]
            
            # 중복 제거하고 병합
            post_ids = set([p.id for p in queryset] + [p.id for p in popular_posts])
            queryset = self.get_queryset().filter(id__in=post_ids)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_exercise(self, request):
        """운동 유형별 게시물"""
        exercise_type = request.query_params.get('type', '')
        
        if not exercise_type:
            return Response(
                {'error': 'Exercise type is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            Q(exercise_name__icontains=exercise_type) |
            Q(content__icontains=exercise_type),
            visibility='public'
        ).order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SocialCommentViewSet(viewsets.ModelViewSet):
    """댓글 ViewSet"""
    queryset = SocialComment.objects.all()
    serializer_class = SocialCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return SocialComment.objects.select_related('user', 'post').prefetch_related('replies')
    
    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)
        
        # 알림 생성 (본인 제외)
        if comment.post.user != self.request.user:
            notification = SocialNotification.objects.create(
                user=comment.post.user,
                from_user=self.request.user,
                type='comment',
                title='새로운 댓글',
                message=f'{self.request.user.username}님이 댓글을 남겼습니다: {comment.content[:50]}',
                post=comment.post
            )
            # WebSocket으로 실시간 알림 전송
            send_notification_to_user(comment.post.user.id, {
                'id': notification.id,
                'type': 'comment',
                'title': notification.title,
                'message': notification.message,
                'from_user': {
                    'id': self.request.user.id,
                    'username': self.request.user.username,
                    'avatar_url': self.request.user.profile_image.url if hasattr(self.request.user, 'profile_image') and self.request.user.profile_image else None
                },
                'post_id': comment.post.id,
                'created_at': notification.created_at.isoformat()
            })
    
    def perform_update(self, serializer):
        # 본인 댓글만 수정 가능
        if self.get_object().user != self.request.user:
            raise permissions.PermissionDenied("본인의 댓글만 수정할 수 있습니다.")
        serializer.save()
    
    def perform_destroy(self, instance):
        # 본인 댓글만 삭제 가능
        if instance.user != self.request.user:
            raise permissions.PermissionDenied("본인의 댓글만 삭제할 수 있습니다.")
        instance.delete()


class SocialFriendRequestViewSet(viewsets.ModelViewSet):
    """친구 요청 ViewSet"""
    serializer_class = SocialFriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SocialFriendRequest.objects.filter(
            Q(from_user=self.request.user) | Q(to_user=self.request.user)
        ).select_related('from_user', 'to_user')
    
    def perform_create(self, serializer):
        to_user = serializer.validated_data['to_user']
        
        # 자기 자신에게 요청 불가
        if to_user == self.request.user:
            raise serializers.ValidationError("자기 자신에게 친구 요청을 보낼 수 없습니다.")
        
        # 이미 친구 요청이 있는지 확인
        existing = SocialFriendRequest.objects.filter(
            Q(from_user=self.request.user, to_user=to_user) |
            Q(from_user=to_user, to_user=self.request.user)
        ).exists()
        
        if existing:
            raise serializers.ValidationError("이미 친구 요청이 존재합니다.")
        
        friend_request = serializer.save(from_user=self.request.user)
        
        # 알림 생성
        notification = SocialNotification.objects.create(
            user=to_user,
            from_user=self.request.user,
            type='friend_request',
            title='새로운 친구 요청',
            message=f'{self.request.user.username}님이 친구 요청을 보냈습니다.'
        )
        # WebSocket으로 실시간 알림 전송
        send_notification_to_user(to_user.id, {
            'id': notification.id,
            'type': 'friend_request',
            'title': notification.title,
            'message': notification.message,
            'from_user': {
                'id': self.request.user.id,
                'username': self.request.user.username,
                'avatar_url': self.request.user.profile_image.url if hasattr(self.request.user, 'profile_image') and self.request.user.profile_image else None
            },
            'created_at': notification.created_at.isoformat()
        })
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """친구 요청 수락"""
        friend_request = self.get_object()
        
        if friend_request.to_user != request.user:
            return Response({'error': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        if friend_request.status != 'pending':
            return Response({'error': '이미 처리된 요청입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        friend_request.status = 'accepted'
        friend_request.responded_at = timezone.now()
        friend_request.save()
        
        # 양방향 팔로우 설정
        from_profile, _ = SocialProfile.objects.get_or_create(user=friend_request.from_user)
        to_profile, _ = SocialProfile.objects.get_or_create(user=friend_request.to_user)
        
        from_profile.followers.add(friend_request.to_user)
        to_profile.followers.add(friend_request.from_user)
        
        return Response({'status': 'accepted'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """친구 요청 거절"""
        friend_request = self.get_object()
        
        if friend_request.to_user != request.user:
            return Response({'error': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        if friend_request.status != 'pending':
            return Response({'error': '이미 처리된 요청입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        friend_request.status = 'rejected'
        friend_request.responded_at = timezone.now()
        friend_request.save()
        
        return Response({'status': 'rejected'})


class SocialNotificationViewSet(viewsets.ModelViewSet):
    """알림 ViewSet"""
    serializer_class = SocialNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SocialNotification.objects.filter(user=self.request.user).select_related('from_user', 'post')
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """알림 읽음 처리"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """모든 알림 읽음 처리"""
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """읽지 않은 알림 개수"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})


class StoryViewSet(viewsets.ModelViewSet):
    """스토리 ViewSet"""
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 만료되지 않은 스토리만 반환
        return Story.objects.filter(
            expires_at__gt=timezone.now()
        ).select_related('user').prefetch_related('views', 'reactions')
    
    def perform_create(self, serializer):
        # 미디어 타입을 먼저 설정
        validated_data = {}
        if 'media_file' in serializer.validated_data:
            media_file = serializer.validated_data['media_file']
            content_type = getattr(media_file, 'content_type', '')
            
            if content_type == 'image/gif':
                validated_data['media_type'] = 'gif'
            elif content_type.startswith('image'):
                validated_data['media_type'] = 'image'
            elif content_type.startswith('video'):
                validated_data['media_type'] = 'video'
        
        # user와 media_type을 함께 저장
        story = serializer.save(user=self.request.user, **validated_data)
    
    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        """스토리 조회 기록"""
        story = self.get_object()
        
        # 스토리 조회 기록 생성 (중복 방지)
        StoryView.objects.get_or_create(
            story=story,
            viewer=request.user
        )
        
        serializer = self.get_serializer(story)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """스토리에 반응 보내기"""
        story = self.get_object()
        
        emoji = request.data.get('emoji')
        message = request.data.get('message')
        
        if not emoji and not message:
            return Response(
                {'error': '이모지 또는 메시지를 입력해주세요.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reaction = StoryReaction.objects.create(
            story=story,
            user=request.user,
            emoji=emoji,
            message=message
        )
        
        # 스토리 작성자에게 알림 전송
        if story.user != request.user:
            notification_message = f'{request.user.username}님이 스토리에 반응했습니다'
            if emoji:
                notification_message += f': {emoji}'
            if message:
                notification_message += f' "{message[:50]}"'
            
            notification = SocialNotification.objects.create(
                user=story.user,
                from_user=request.user,
                type='comment',  # story_reaction 타입이 없으므로 comment 사용
                title='스토리 반응',
                message=notification_message
            )
            
            # WebSocket으로 실시간 알림 전송
            send_notification_to_user(story.user.id, {
                'id': notification.id,
                'type': 'story_reaction',
                'title': notification.title,
                'message': notification.message,
                'from_user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'avatar_url': request.user.profile_image.url if hasattr(request.user, 'profile_image') and request.user.profile_image else None
                },
                'story_id': story.id,
                'created_at': notification.created_at.isoformat()
            })
        
        serializer = StoryReactionSerializer(reaction)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def user_stories(self, request):
        """사용자별 스토리 목록 (팔로잉한 사용자들)"""
        # 현재 사용자 + 팔로잉한 사용자들
        try:
            # 현재 사용자가 팔로우하는 사용자들
            following_profiles = SocialProfile.objects.filter(
                followers=request.user
            ).values_list('user', flat=True)
            
            users_with_stories = User.objects.filter(
                Q(id=request.user.id) | Q(id__in=following_profiles)
            ).filter(
                stories__expires_at__gt=timezone.now()
            ).distinct().prefetch_related(
                Prefetch(
                    'stories',
                    queryset=Story.objects.filter(expires_at__gt=timezone.now()).order_by('-created_at')
                )
            )
            
            # 본인을 맨 앞에 배치
            ordered_users = []
            current_user = None
            
            for user in users_with_stories:
                if user.id == request.user.id:
                    current_user = user
                else:
                    ordered_users.append(user)
            
            if current_user:
                ordered_users.insert(0, current_user)
            
            serializer = UserStoriesSerializer(ordered_users, many=True, context={'request': request})
            return Response(serializer.data)
        except:
            # 오류 발생 시 현재 사용자의 스토리만 반환
            users_with_stories = User.objects.filter(
                id=request.user.id,
                stories__expires_at__gt=timezone.now()
            ).distinct()
            
            serializer = UserStoriesSerializer(users_with_stories, many=True, context={'request': request})
            return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_stories(self, request):
        """내 스토리 목록"""
        queryset = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def viewers(self, request, pk=None):
        """스토리 조회자 목록 (작성자만 조회 가능)"""
        story = self.get_object()
        
        if story.user != request.user:
            return Response(
                {'error': '스토리 조회자 목록은 작성자만 볼 수 있습니다.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        views = story.views.all().select_related('viewer')
        serializer = StoryViewSerializer(views, many=True, context={'request': request})
        return Response(serializer.data)
    
    def perform_destroy(self, instance):
        # 본인 스토리만 삭제 가능
        if instance.user != self.request.user:
            raise permissions.PermissionDenied("본인의 스토리만 삭제할 수 있습니다.")
        instance.delete()
