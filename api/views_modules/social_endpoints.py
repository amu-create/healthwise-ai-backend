from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime
import random

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
