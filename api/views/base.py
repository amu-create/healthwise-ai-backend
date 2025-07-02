from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
def test_api(request):
    return Response({'message': 'API is working!', 'method': request.method})

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """DB 연결 상태를 확인하는 헬스체크 엔드포인트"""
    import django.db
    from django.db import connection
    
    result = {
        'status': 'ok',
        'api': 'running',
        'timestamp': datetime.now().isoformat(),
    }
    
    # DB 연결 테스트
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        result['database'] = 'connected'
        
        # 사용자 수 확인
        user_count = User.objects.count()
        result['users'] = user_count
        
        # 세션 테스트
        result['session_key'] = request.session.session_key or 'no-session'
        
    except Exception as e:
        result['database'] = 'error'
        result['db_error'] = str(e)
        result['status'] = 'error'
    
    # Redis 연결 테스트
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            result['redis'] = 'connected'
        else:
            result['redis'] = 'not working'
    except Exception as e:
        result['redis'] = 'error'
        result['redis_error'] = str(e)
    
    return Response(result)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def api_health(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return Response({
        'status': 'healthy',
        'service': 'api',
        'version': '1.0.0'
    })
