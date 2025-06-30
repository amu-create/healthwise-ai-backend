# WebSocket URL patterns for social features
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Notification WebSocket
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    
    # Direct Message WebSocket
    re_path(r'ws/dm/$', consumers.DirectMessageConsumer.as_asgi()),
    re_path(r'ws/dm/(?P<conversation_id>\d+)/$', consumers.DirectMessageConsumer.as_asgi()),
]
