from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.utils import timezone
import random

@api_view(['GET'])
@permission_classes([AllowAny])
def social_feed(request):
    """소셜 피드 (게스트도 접근 가능)"""
    # 목 데이터 생성
    posts = []
    for i in range(10):
        posts.append({
            'id': i + 1,
            'author': {
                'id': random.randint(1, 100),
                'username': f'user{random.randint(1, 100)}',
                'profile_image': None
            },
            'content': f'운동 {random.randint(30, 120)}분 완료! 💪',
            'created_at': (timezone.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
            'likes_count': random.randint(0, 50),
            'comments_count': random.randint(0, 20),
            'is_liked': False
        })
    
    return Response({
        'posts': posts,
        'total': len(posts),
        'page': 1,
        'has_next': False
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def social_posts_feed(request):
    """소셜 포스트 피드"""
    # 목 데이터 생성
    posts = []
    for i in range(10):
        posts.append({
            'id': i + 1,
            'author': {
                'id': random.randint(1, 100),
                'username': f'user{random.randint(1, 100)}',
                'profile_image': None
            },
            'content': f'운동 {random.randint(30, 120)}분 완료! 💪',
            'created_at': (timezone.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
            'likes_count': random.randint(0, 50),
            'comments_count': random.randint(0, 20),
            'is_liked': False
        })
    
    return Response({
        'posts': posts,
        'total': len(posts),
        'page': 1,
        'has_next': False
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def social_posts_create(request):
    """새 포스트 작성"""
    data = request.data
    
    # 간단한 검증
    if not data.get('content'):
        return Response({
            'error': 'Content is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 목 응답
    new_post = {
        'id': random.randint(100, 999),
        'author': {
            'id': request.user.id,
            'username': request.user.username,
            'profile_image': None
        },
        'content': data['content'],
        'created_at': timezone.now().isoformat(),
        'likes_count': 0,
        'comments_count': 0,
        'is_liked': False
    }
    
    return Response(new_post, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([AllowAny])
def social_posts_popular(request):
    """인기 포스트"""
    posts = []
    for i in range(5):
        posts.append({
            'id': i + 1,
            'author': {
                'id': random.randint(1, 100),
                'username': f'popular_user{random.randint(1, 20)}',
                'profile_image': None
            },
            'content': f'오늘의 운동 완료! 🏃‍♂️ #{random.choice(["헬스", "러닝", "요가", "필라테스"])}',
            'created_at': (timezone.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
            'likes_count': random.randint(100, 500),
            'comments_count': random.randint(20, 100),
            'is_liked': False
        })
    
    return Response({
        'posts': posts,
        'total': len(posts)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def social_posts_recommended(request):
    """추천 포스트"""
    posts = []
    for i in range(8):
        posts.append({
            'id': i + 100,
            'author': {
                'id': random.randint(1, 100),
                'username': f'recommend_user{random.randint(1, 30)}',
                'profile_image': None
            },
            'content': f'운동 팁: {random.choice(["물을 충분히 마시세요", "스트레칭을 잊지 마세요", "휴식도 중요해요", "꾸준함이 핵심입니다"])}',
            'created_at': (timezone.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
            'likes_count': random.randint(30, 200),
            'comments_count': random.randint(5, 50),
            'is_liked': False
        })
    
    return Response({
        'posts': posts,
        'total': len(posts)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def social_stories(request):
    """스토리 목록"""
    stories = []
    for i in range(10):
        stories.append({
            'id': i + 1,
            'user': {
                'id': random.randint(1, 100),
                'username': f'story_user{random.randint(1, 50)}',
                'profile_image': None
            },
            'preview_image': None,
            'created_at': (timezone.now() - timedelta(hours=random.randint(1, 23))).isoformat(),
            'expires_at': (timezone.now() + timedelta(hours=random.randint(1, 23))).isoformat(),
            'is_viewed': random.choice([True, False])
        })
    
    return Response({
        'stories': stories,
        'total': len(stories)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def social_notifications(request):
    """알림 목록 (게스트도 접근 가능)"""
    notifications = []
    notification_types = ['like', 'comment', 'follow', 'mention']
    
    for i in range(15):
        notification_type = random.choice(notification_types)
        notifications.append({
            'id': i + 1,
            'type': notification_type,
            'message': f'{random.choice(["user1", "user2", "user3"])}님이 회원님의 게시물을 좋아합니다.',
            'created_at': (timezone.now() - timedelta(hours=random.randint(1, 168))).isoformat(),
            'is_read': random.choice([True, False]),
            'related_user': {
                'id': random.randint(1, 100),
                'username': f'user{random.randint(1, 100)}',
                'profile_image': None
            }
        })
    
    return Response({
        'notifications': notifications,
        'total': len(notifications),
        'unread_count': len([n for n in notifications if not n['is_read']])
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def social_notifications_unread_count(request):
    """읽지 않은 알림 개수 (게스트도 접근 가능)"""
    return Response({
        'unread_count': random.randint(0, 10)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_post(request, post_id):
    """포스트 좋아요"""
    action = request.data.get('action', 'like')
    
    if action not in ['like', 'unlike']:
        return Response({
            'error': 'Invalid action'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'action': action,
        'post_id': post_id,
        'likes_count': random.randint(1, 100)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def social_unread_count(request):
    """읽지 않은 소셜 알림 수 (게스트도 접근 가능)"""
    return Response({
        'messages': random.randint(0, 5),
        'notifications': random.randint(0, 10),
        'total': random.randint(0, 15)
    })

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def mark_all_notifications_as_read(request):
    """모든 알림을 읽음으로 표시"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        # 게스트 사용자 확인
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': '로그인이 필요합니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # TODO: 실제 데이터베이스 업데이트 로직
        # Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        
        return Response({
            'success': True,
            'message': '모든 알림을 읽음으로 표시했습니다.',
            'updated_count': random.randint(1, 5)  # 임시 값
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error marking notifications as read: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def upload_profile_image(request):
    """프로필 이미지 업로드"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        # 게스트 사용자 확인
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': '로그인이 필요합니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 파일 확인
        if 'image' not in request.FILES:
            return Response({
                'success': False,
                'error': '이미지 파일이 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        
        # 파일 크기 확인 (5MB 제한)
        if image_file.size > 5 * 1024 * 1024:
            return Response({
                'success': False,
                'error': '파일 크기는 5MB를 초과할 수 없습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 파일 타입 확인
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if image_file.content_type not in allowed_types:
            return Response({
                'success': False,
                'error': '지원하지 않는 파일 형식입니다. (JPEG, PNG, WebP만 가능)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # TODO: 실제 파일 업로드 처리 (S3 또는 로컬 스토리지)
        # 여기서는 임시로 URL만 생성
        image_url = f'/media/profiles/{request.user.id}_{image_file.name}'
        
        # 프로필 업데이트
        # if hasattr(request.user, 'profile'):
        #     request.user.profile.profile_image = image_url
        #     request.user.profile.save()
        
        return Response({
            'success': True,
            'message': '프로필 이미지가 업로드되었습니다.',
            'image_url': image_url,
            'profile_image': image_url
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error uploading profile image: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 추가 소셜 기능들
@api_view(['GET'])
@permission_classes([AllowAny])
def social_conversations_unread_count(request):
    """읽지 않은 대화 개수 (게스트도 접근 가능)"""
    return Response({
        'unread_count': random.randint(0, 5)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def social_posts_list(request):
    """포스트 목록"""
    return social_posts_feed(request)
