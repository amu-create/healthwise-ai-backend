from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.api.utils.location import get_location_by_ip, get_client_ip


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_location(request):
    """
    사용자의 위치 정보 가져오기
    HTTPS가 아닌 환경에서는 IP 기반 위치 제공
    """
    # 클라이언트 IP 가져오기
    client_ip = get_client_ip(request)
    
    # IP 기반 위치 정보 가져오기
    location = get_location_by_ip(client_ip)
    
    return Response({
        'location': location,
        'method': 'ip_based',
        'message': 'HTTPS가 필요한 정확한 GPS 위치 대신 IP 기반 대략적인 위치를 제공합니다.'
    })
