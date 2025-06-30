from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def test_login(request):
    """테스트용 로그인 뷰 - 세션 쿠키 확인"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    user = authenticate(request, username=email, password=password)
    
    if user:
        login(request, user)
        
        # 세션 정보 확인
        session_info = {
            'session_key': request.session.session_key,
            'is_new': request.session.is_new(),
            'exists': request.session.exists(request.session.session_key) if request.session.session_key else False,
            'cookies': dict(request.COOKIES),
            'session_cookie_name': request.session.cookie_name,
            'session_cookie_domain': request.session.cookie_domain,
            'session_cookie_path': request.session.cookie_path,
            'session_cookie_secure': request.session.cookie_secure,
            'session_cookie_httponly': request.session.cookie_httponly,
            'session_cookie_samesite': request.session.cookie_samesite,
        }
        
        logger.info(f"Session info: {session_info}")
        
        response = Response({
            'message': '로그인 성공',
            'user_id': user.id,
            'email': user.email,
            'session_info': session_info
        })
        
        # 명시적으로 세션 쿠키 설정
        response.set_cookie(
            key='sessionid',
            value=request.session.session_key,
            max_age=None,  # 브라우저 종료 시까지
            expires=None,
            path='/',
            domain=None,  # 현재 도메인
            secure=False,  # HTTP에서도 전송
            httponly=True,
            samesite='Lax'
        )
        
        return response
    else:
        return Response({
            'error': '인증 실패'
        }, status=401)
