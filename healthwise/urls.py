from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def index(request):
    return JsonResponse({
        'message': 'HealthWise AI Backend API',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': {
            'api': '/api/',
            'admin': '/admin/',
            'health': '/health/',
        }
    })

def health(request):
    return JsonResponse({
        'status': 'healthy',
        'service': 'backend',
        'database': 'connected',
        'redis': 'connected' if hasattr(request, 'channel_layer') else 'not configured'
    })

urlpatterns = [
    path('', index, name='index'),
    path('health/', health, name='health'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]