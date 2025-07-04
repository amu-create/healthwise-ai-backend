"""
JWT 기반 인증 시스템 구현
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
    사용자 정보 응답 생성
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
        'tokens': tokens,
        'isAuthenticated': True
    }


def authenticate_user(username=None, email=None, password=None):
    """
    사용자 인증 헬퍼 함수
    """
    if email:
        # 이메일로 로그인 시도
        try:
            user = User.objects.get(email=email)
            username = user.username
        except User.DoesNotExist:
            return None
    
    # Django 기본 인증 사용
    user = authenticate(username=username, password=password)
    
    if user and user.is_active:
        # 프로필 자동 생성
        from .models import UserProfile
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)
        return user
    
    return None
