# views/__init__.py
# auth.py에서 모든 뷰를 import
from .auth import (
    RegisterView, LoginView, LogoutView, UserProfileView,
    ChangePasswordView, health_options, check_email, get_csrf_token,
    ChatbotView, clear_chat_history, chatbot_status, daily_recommendations,
    ChatSessionView
)

# image_proxy.py에서 import
from .image_proxy import ImageProxyView

# 모든 것을 재export
__all__ = [
    'RegisterView', 'LoginView', 'LogoutView', 'UserProfileView',
    'ChangePasswordView', 'health_options', 'check_email', 'get_csrf_token',
    'ChatbotView', 'clear_chat_history', 'chatbot_status', 'daily_recommendations',
    'ChatSessionView', 'ImageProxyView'
]
