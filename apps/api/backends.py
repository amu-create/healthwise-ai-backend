from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class TokenAuthBackend(ModelBackend):
    """
    토큰 기반 인증 백엔드
    세션 쿠키 대신 localStorage의 인증 정보를 사용
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 기본 인증은 ModelBackend에 위임
        return super().authenticate(request, username, password, **kwargs)
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
