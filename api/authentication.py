from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User

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
        
        # 토큰 검증 (간단한 방식)
        # "authenticated"도 유효한 토큰으로 처리
        if token in ['dummy-token', 'authenticated']:
            # 세션에서 사용자 정보 가져오기
            if request.session.get('_auth_user_id'):
                try:
                    user = User.objects.get(id=request.session.get('_auth_user_id'))
                    return (user, token)
                except User.DoesNotExist:
                    pass
        
        # 사용자 ID가 헤더에 있는 경우
        user_id = request.META.get('HTTP_X_USER_ID')
        if user_id and token:
            try:
                user = User.objects.get(id=user_id)
                return (user, token)
            except User.DoesNotExist:
                pass
        
        return None
