from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..services.data import HEALTH_OPTIONS

# 건강 선택지 API
@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def health_options(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return Response(HEALTH_OPTIONS)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def api_health(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return Response({
        'status': 'healthy',
        'service': 'api',
        'version': '1.0.0'
    })
