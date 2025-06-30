from rest_framework import viewsets, status, permissions
from .notification_service import NotificationService
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Prefetch
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
import os
from .models import (
    UserProfile, Follow, FriendRequest, WorkoutPost,
    PostLike, PostComment
)
from .serializers_social import (
    UserProfileSerializer, UserSocialSerializer, FollowSerializer,
    FriendRequestSerializer, WorkoutPostSerializer, WorkoutPostDetailSerializer,
    CommentSerializer, PostLikeSerializer
)
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator

User = get_user_model()


class UserProfileViewSet(viewsets.ModelViewSet):
    """사용자 프로필 뷰셋"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 자신의 프로필 또는 공개 프로필만 조회 가능
        if self.action == 'list':
            # 공개 프로필 목록
            return UserProfile.objects.filter(
                privacy_setting='public'
            ).select_related('user')
        return UserProfile.objects.all()
    
    def get_object(self):
        # username으로 프로필 조회
        username = self.kwargs.get('pk')
        try:
            # 숫자인 경우 ID로 조회
            user_id = int(username)
            user = get_object_or_404(User, id=user_id)
        except ValueError:
            # 문자열인 경우 username으로 조회
            user = get_object_or_404(User, username=username)
        
        profile, created = UserProfile.objects.get_or_create(user=user)
        self.check_object_permissions(self.request, profile)
        return profile
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """현재 사용자의 프로필"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """사용자 팔로우"""
        profile = self.get_object()
        target_user = profile.user
        
        if request.user == target_user:
            return Response(
                {'error': '자기 자신을 팔로우할 수 없습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target_user
        )
        
        if created:
            # 팔로우 알림 발송
            NotificationService.send_follow_notification(request.user, target_user)
            return Response({'message': '팔로우했습니다.'}, status=status.HTTP_201_CREATED)
        
        return Response({'message': '이미 팔로우 중입니다.'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        """팔로우 취소"""
        profile = self.get_object()
        target_user = profile.user
        
        try:
            follow = Follow.objects.get(
                follower=request.user,
                following=target_user
            )
            follow.delete()
            return Response({'message': '팔로우를 취소했습니다.'})
        except Follow.DoesNotExist:
            return Response(
                {'error': '팔로우하고 있지 않습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        """팔로워 목록"""
        profile = self.get_object()
        followers = User.objects.filter(
            following__following=profile.user
        ).select_related('social_profile')
        
        serializer = UserSocialSerializer(
            followers, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        """팔로잉 목록"""
        profile = self.get_object()
        following = User.objects.filter(
            followers__follower=profile.user
        ).select_related('social_profile')
        
        serializer = UserSocialSerializer(
            following, many=True, context={'request': request}
        )
        return Response(serializer.data)


class FriendRequestViewSet(viewsets.ModelViewSet):
    """친구 요청 관리"""
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # 보낸 요청과 받은 요청 모두 조회
        return FriendRequest.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        ).select_related('from_user', 'to_user')
    
    def create(self, serializer):
        to_username = self.request.data.get('to_username')
        to_user = get_object_or_404(User, username=to_username)
        
        if self.request.user == to_user:
            return Response(
                {'error': '자기 자신에게 친구 요청을 보낼 수 없습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 이미 친구 요청이 있는지 확인
        existing_request = FriendRequest.objects.filter(
            Q(from_user=self.request.user, to_user=to_user) |
            Q(from_user=to_user, to_user=self.request.user)
        ).first()
        
        if existing_request:
            return Response(
                {'error': '이미 친구 요청이 존재합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(from_user=self.request.user, to_user=to_user)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """친구 요청 수락"""
        friend_request = self.get_object()
        
        if friend_request.to_user != request.user:
            return Response(
                {'error': '권한이 없습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            # 친구 요청 상태 변경
            friend_request.status = 'accepted'
            friend_request.save()
            
            # 양방향 팔로우 관계 생성
            Follow.objects.get_or_create(
                follower=friend_request.from_user,
                following=friend_request.to_user
            )
            Follow.objects.get_or_create(
                follower=friend_request.to_user,
                following=friend_request.from_user
            )
        
        return Response({'message': '친구 요청을 수락했습니다.'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """친구 요청 거절"""
        friend_request = self.get_object()
        
        if friend_request.to_user != request.user:
            return Response(
                {'error': '권한이 없습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        friend_request.status = 'rejected'
        friend_request.save()
        
        return Response({'message': '친구 요청을 거절했습니다.'})


class WorkoutPostViewSet(viewsets.ModelViewSet):
    """운동 게시물 뷰셋"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WorkoutPostDetailSerializer
        return WorkoutPostSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # 기본적으로 공개 게시물과 팔로우하는 사용자의 게시물
        queryset = WorkoutPost.objects.filter(
            Q(visibility='public') |
            Q(user=user) |
            Q(visibility='followers', user__followers__follower=user)
        ).select_related(
            'user', 'user__social_profile', 'workout_log', 'workout_log__routine'
        ).prefetch_related(
            Prefetch('comments', queryset=PostComment.objects.select_related('user'))
        ).distinct()
        
        # 피드 타입에 따른 필터링
        feed_type = self.request.query_params.get('feed_type', 'all')
        if feed_type == 'following':
            # 팔로잉하는 사용자의 게시물만
            queryset = queryset.filter(user__followers__follower=user)
        elif feed_type == 'my':
            # 내 게시물만
            queryset = queryset.filter(user=user)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        # 파일 크기 및 형식 검증
        media_file = self.request.FILES.get('media')
        if media_file:
            # 파일 크기 검증
            file_ext = os.path.splitext(media_file.name)[1].lower()
            
            if file_ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                if media_file.size > 10 * 1024 * 1024:  # 10MB
                    raise ValidationError('이미지 파일 크기는 10MB 이하여야 합니다.')
            elif file_ext in ['.mp4', '.webm', '.mov']:
                if media_file.size > 50 * 1024 * 1024:  # 50MB
                    raise ValidationError('동영상 파일 크기는 50MB 이하여야 합니다.')
                # TODO: 동영상 길이 검증 (8초)
            else:
                raise ValidationError('지원하지 않는 파일 형식입니다.')
        
        instance = serializer.save(user=self.request.user)
        
        # 미디어 파일이 있으면 URL 생성
        if instance.media_file:
            request = self.request
            instance.media_url = request.build_absolute_uri(instance.media_file.url)
            instance.save()
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """게시물 좋아요"""
        post = self.get_object()
        
        like, created = PostLike.objects.get_or_create(
            user=request.user,
            post=post
        )
        
        if created:
            # 좋아요 수 증가
            post.likes_count = post.likes.count()
            post.save()
            
            # 좋아요 알림 발송
            NotificationService.send_like_notification(request.user, post)
            
            return Response({'message': '좋아요를 눌렀습니다.'}, status=status.HTTP_201_CREATED)
        
        return Response({'message': '이미 좋아요를 눌렀습니다.'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """좋아요 취소"""
        post = self.get_object()
        
        try:
            like = PostLike.objects.get(user=request.user, post=post)
            like.delete()
            
            # 좋아요 수 감소
            post.likes_count = post.likes.count()
            post.save()
            
            return Response({'message': '좋아요를 취소했습니다.'})
        except PostLike.DoesNotExist:
            return Response(
                {'error': '좋아요를 누르지 않았습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def likes(self, request, pk=None):
        """좋아요 누른 사용자 목록"""
        post = self.get_object()
        likes = PostLike.objects.filter(post=post).select_related('user')
        
        users = [like.user for like in likes]
        serializer = UserSocialSerializer(
            users, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        """댓글 작성"""
        post = self.get_object()
        content = request.data.get('content')
        parent_id = request.data.get('parent_id')
        
        if not content:
            return Response(
                {'error': '댓글 내용을 입력해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment_data = {
            'user': request.user,
            'post': post,
            'content': content
        }
        
        if parent_id:
            parent_comment = get_object_or_404(PostComment, id=parent_id, post=post)
            comment_data['parent'] = parent_comment
        
        comment = PostComment.objects.create(**comment_data)
        
        # 댓글 수 업데이트
        post.comments_count = post.comments.filter(parent__isnull=True).count()
        post.save()
        
        # 댓글 알림 발송
        NotificationService.send_comment_notification(request.user, comment)
        
        serializer = CommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def feed(self, request):
        """개인화된 피드"""
        page = request.query_params.get('page', 1)
        page_size = 10
        
        queryset = self.get_queryset()
        paginator = Paginator(queryset, page_size)
        
        try:
            posts = paginator.page(page)
        except:
            posts = []
        
        serializer = self.get_serializer(posts, many=True)
        
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page
        })


class CommentViewSet(viewsets.ModelViewSet):
    """댓글 관리"""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PostComment.objects.filter(
            user=self.request.user
        ).select_related('user', 'post')
    
    def update(self, request, *args, **kwargs):
        """댓글 수정"""
        comment = self.get_object()
        
        if comment.user != request.user:
            return Response(
                {'error': '권한이 없습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """댓글 삭제"""
        comment = self.get_object()
        
        if comment.user != request.user:
            return Response(
                {'error': '권한이 없습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        post = comment.post
        response = super().destroy(request, *args, **kwargs)
        
        # 댓글 수 업데이트
        post.comments_count = post.comments.filter(parent__isnull=True).count()
        post.save()
        
        return response
