from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.cache import cache
from django.conf import settings
import logging
from .guest_utils import reset_guest_usage, get_guest_usage_info, get_or_create_guest_id

logger = logging.getLogger(__name__)

# 개발 환경에서만 사용할 수 있는 리셋 API
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_guest_limits(request):
    """게스트 사용 제한 리셋 (개발/테스트용)"""
    
    # 프로덕션 환경에서는 비활성화
    if not settings.DEBUG:
        return Response({
            'error': 'This endpoint is only available in development mode'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 게스트 ID 가져오기
    guest_id = get_or_create_guest_id(request)
    
    # 리셋 수행
    success = reset_guest_usage(request)
    
    # 현재 사용 정보 가져오기
    usage_info, _ = get_guest_usage_info(request)
    
    return Response({
        'message': '게스트 사용 제한이 초기화되었습니다.',
        'guest_id': guest_id,
        'success': success,
        'current_usage': usage_info
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_guest_usage_status(request):
    """현재 게스트 사용 현황 확인 (개발/테스트용)"""
    
    if not settings.DEBUG:
        return Response({
            'error': 'This endpoint is only available in development mode'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 게스트 사용 정보 가져오기
    usage_info, guest_id = get_guest_usage_info(request)
    
    from datetime import datetime
    today = datetime.now().strftime('%Y%m%d')
    
    return Response({
        'guest_id': guest_id,
        'date': today,
        'usage': usage_info
    }, status=status.HTTP_200_OK)
