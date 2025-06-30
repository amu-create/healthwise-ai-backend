import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)
User = get_user_model()

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 요청 로깅
        logger.info(f"Request: {request.method} {request.path}")
        if request.path.startswith('/api/chatbot'):
            logger.info(f"Chatbot request from: {request.user}")
            logger.info(f"Is authenticated: {request.user.is_authenticated}")
            logger.info(f"Request headers: {dict(request.headers)}")
            
        response = self.get_response(request)
        
        # 응답 로깅
        if request.path.startswith('/api/chatbot'):
            logger.info(f"Response status: {response.status_code}")
            
        return response


class AuthenticatedUserMiddleware:
    """
    localStorage의 isAuthenticated 플래그를 확인하여 사용자 인증
    세션 쿠키가 없어도 인증된 사용자로 처리
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # X-Auth-User 헤더로 사용자 ID 전달
        auth_user_id = request.headers.get('X-Auth-User')
        
        if auth_user_id and not request.user.is_authenticated:
            try:
                user = User.objects.get(id=auth_user_id)
                request.user = user
                request._cached_user = user
                logger.debug(f"Authenticated user {user.email} via X-Auth-User header")
            except User.DoesNotExist:
                logger.warning(f"Invalid user ID in X-Auth-User header: {auth_user_id}")
        
        response = self.get_response(request)
        return response
