from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Exists, OuterRef
from django.contrib.auth import get_user_model
from ..models import (
    UserProfile, Follow, FriendRequest, 
    WorkoutPost, PostLike, PostComment
)
from ..serializers.social import (
    UserProfileSerializer, WorkoutPostSerializer,
    CommentSerializer, FriendRequestSerializer
)

User = get_user_model()

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = UserProfile.objects.select_related('user')
        
        # 프라이버시 설정에 따른 필터링
        if not user.is_staff:
            queryset = queryset.filter(
                Q(privacy_setting='public') |
                Q(user=user) |
                Q(user__followers__follower=user, privacy_setting='followers')
            )
        
        return queryset
    
    def get_object(self):
        username = self.kwargs.get('pk')
        user = get_object_or_404(User, username=username)
        return get_object_or_404(UserProfile, user=user)
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        profile = self.get_object()
        if profile.user == request.user:
            return Response(
                {'error': 'Cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        Follow.objects.get_or_create(
            follower=request.user,
            following=profile.user
        )
        
        return Response({'status': 'following'})
    
    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        profile = self.get_object()
        Follow.objects.filter(
            follower=request.user,
            following=profile.user
        ).delete()
        
        return Response({'status': 'unfollowed'})


class FriendRequestViewSet(viewsets.ModelViewSet):
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return FriendRequest.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        ).select_related('from_user', 'to_user')
    
    def create(self, request):
        to_user_id = request.data.get('to_user')
        to_user = get_object_or_404(User, id=to_user_id)
        
        if to_user == request.user:
            return Response(
                {'error': 'Cannot send friend request to yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 이미 친구 요청이 있는지 확인
        existing = FriendRequest.objects.filter(
            Q(from_user=request.user, to_user=to_user) |
            Q(from_user=to_user, to_user=request.user)
        ).first()
        
        if existing:
            return Response(
                {'error': 'Friend request already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        friend_request = FriendRequest.objects.create(
            from_user=request.user,
            to_user=to_user
        )
        
        serializer = self.get_serializer(friend_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        friend_request = self.get_object()
        if friend_request.to_user != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        friend_request.is_accepted = True
        friend_request.save()
        
        # 양방향 팔로우 생성
        Follow.objects.get_or_create(
            follower=friend_request.from_user,
            following=friend_request.to_user
        )
        Follow.objects.get_or_create(
            follower=friend_request.to_user,
            following=friend_request.from_user
        )
        
        return Response({'status': 'accepted'})
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        friend_request = self.get_object()
        if friend_request.to_user != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        friend_request.delete()
        return Response({'status': 'declined'})


class WorkoutPostViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = WorkoutPost.objects.select_related(
            'user', 'user__userprofile'
        ).prefetch_related(
            'likes', 'comments'
        ).annotate(
            likes_count=Count('likes'),
            comments_count=Count('comments'),
            is_liked=Exists(
                PostLike.objects.filter(
                    post=OuterRef('pk'),
                    user=user
                )
            )
        )
        
        # 프라이버시 설정에 따른 필터링
        queryset = queryset.filter(
            Q(visibility='public') |
            Q(user=user) |
            Q(visibility='followers', user__followers__follower=user)
        )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def feed(self, request):
        """피드 타입별 게시물 조회"""
        feed_type = request.query_params.get('feed_type', 'all')
        queryset = self.get_queryset()
        
        if feed_type == 'following':
            # 팔로잉한 사용자의 게시물만
            following_users = Follow.objects.filter(
                follower=request.user
            ).values_list('following', flat=True)
            queryset = queryset.filter(user__in=following_users)
        elif feed_type == 'my':
            # 내 게시물만
            queryset = queryset.filter(user=request.user)
        
        # 페이지네이션
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = PostLike.objects.get_or_create(
            post=post,
            user=request.user
        )
        
        if created:
            post.likes_count += 1
            post.save()
            return Response({'liked': True})
        
        return Response({'liked': True, 'already_liked': True})
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        post = self.get_object()
        deleted, _ = PostLike.objects.filter(
            post=post,
            user=request.user
        ).delete()
        
        if deleted:
            post.likes_count = max(0, post.likes_count - 1)
            post.save()
            return Response({'liked': False})
        
        return Response({'liked': False, 'was_not_liked': True})
    
    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        post = self.get_object()
        content = request.data.get('content')
        
        if not content:
            return Response(
                {'error': 'Content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = PostComment.objects.create(
            post=post,
            user=request.user,
            content=content
        )
        
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PostComment.objects.filter(
            Q(user=self.request.user) |
            Q(post__user=self.request.user) |
            Q(post__visibility='public') |
            Q(post__visibility='followers', post__user__followers__follower=self.request.user)
        ).select_related('user', 'post')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
