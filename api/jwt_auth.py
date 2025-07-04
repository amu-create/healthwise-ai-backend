"""
JWT 기반 인증 시스템 구현 - 로그인 문제 해결 버전
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import logging

logger = logging.getLogger(__name__)

class CustomJWTAuthentication(JWTAuthentication):
    """
    커스텀 JWT 인증 클래스
    - 게스트 사용자 지원
    - 자동 프로필 생성
    """
    
    def authenticate(self, request):
        # 먼저 JWT 인증 시도
        try:
            result = super().authenticate(request)
            if result:
                user, token = result
                # 프로필 자동 생성
                self._ensure_profile(user)
                return (user, token)
        except Exception as e:
            logger.debug(f"JWT authentication failed: {str(e)}")
        
        # 게스트 사용자 확인
        if request.META.get('HTTP_X_GUEST_ID'):
            return None  # 게스트는 인증 없이 진행
        
        return None
    
    def _ensure_profile(self, user):
        """사용자 프로필 자동 생성"""
        from .models import UserProfile
        if not hasattr(user, 'profile'):
            UserProfile.objects.get_or_create(user=user)


def get_tokens_for_user(user):
    """
    사용자에 대한 JWT 토큰 생성
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def create_user_response(user):
    """
    사용자 정보 응답 생성 - JWT 토큰 포함 (수정된 버전)
    """
    from .serializers import UserSerializer
    from .models import UserProfile
    
    # 프로필 확인 및 생성
    if not hasattr(user, 'profile'):
        UserProfile.objects.create(user=user)
    
    tokens = get_tokens_for_user(user)
    user_data = UserSerializer(user).data
    
    return {
        'user': user_data,
        'access': tokens['access'],  # 프론트엔드가 기대하는 필드명
        'refresh': tokens['refresh'],  # 프론트엔드가 기대하는 필드명
        'tokens': tokens,  # 기존 호환성을 위해 유지
        'isAuthenticated': True
    }


def authenticate_user(username=None, email=None, password=None):
    """
    사용자 인증 헬퍼 함수 - 향상된 로깅
    """
    logger.info(f"Authentication attempt: username={username}, email={email}")
    
    if email:
        # 이메일로 로그인 시도
        try:
            user = User.objects.get(email=email)
            username = user.username
            logger.info(f"Found user by email: {username}")
        except User.DoesNotExist:
            logger.warning(f"No user found with email: {email}")
            return None
    
    # Django 기본 인증 사용
    user = authenticate(username=username, password=password)
    
    if user and user.is_active:
        logger.info(f"Authentication successful for user: {user.username}")
        # 프로필 자동 생성
        from .models import UserProfile
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)
            logger.info(f"Created profile for user: {user.username}")
        return user
    
    logger.warning(f"Authentication failed for username: {username}")
    return None
