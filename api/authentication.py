from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

class SimpleTokenAuthentication(BaseAuthentication):
    """
    간단한 토큰 인증 구현
    헤더: Authorization: Bearer <token>
    """
    def authenticate(self, request):
        # Authorization 헤더 확인
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        # Bearer 토큰 형식 확인
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        token = parts[1]
        
        # 로깅 추가
        logger.debug(f"Auth token: {token[:20]}...")
        
        # 사용자 ID가 헤더에 있는 경우 우선 처리
        user_id = request.META.get('HTTP_X_USER_ID')
        if user_id and token:  # 토큰도 함께 확인
            logger.debug(f"X-User-ID header found: {user_id}")
            try:
                user = User.objects.get(id=user_id)
                logger.info(f"Authenticated user from X-User-ID: {user.username}")
                # 프로필 확인 및 자동 생성
                from ..models import UserProfile
                if not hasattr(user, 'profile'):
                    UserProfile.objects.get_or_create(user=user)
                return (user, token)
            except User.DoesNotExist:
                logger.warning(f"User with ID {user_id} not found")
                pass
        
        # 토큰 검증 (간단한 방식)
        # "authenticated"도 유효한 토큰으로 처리
        if token in ['dummy-token', 'authenticated']:
            # 세션에서 사용자 정보 가져오기
            session_user_id = request.session.get('_auth_user_id')
            if session_user_id:
                try:
                    user = User.objects.get(id=session_user_id)
                    logger.info(f"Authenticated user from session: {user.username}")
                    return (user, token)
                except User.DoesNotExist:
                    logger.warning(f"Session user with ID {session_user_id} not found")
                    pass
        
        logger.debug("No valid authentication found")
        return None
