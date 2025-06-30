"""
위치 관련 유틸리티 함수들
HTTP 환경에서 Geolocation API 대체 방안 제공
"""
import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def get_location_by_ip(ip_address=None):
    """
    IP 주소로 대략적인 위치 정보 가져오기
    """
    if not ip_address:
        return get_default_location()
    
    # 캐시 확인
    cache_key = f"location_ip_{ip_address}"
    cached_location = cache.get(cache_key)
    if cached_location:
        return cached_location
    
    try:
        # ip-api.com 무료 서비스 사용 (하루 45,000 요청 제한)
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                location = {
                    'lat': data.get('lat'),
                    'lng': data.get('lon'),
                    'city': data.get('city'),
                    'country': data.get('country')
                }
                # 24시간 캐싱
                cache.set(cache_key, location, 60 * 60 * 24)
                return location
    except Exception as e:
        logger.error(f"Error getting location by IP: {e}")
    
    return get_default_location()


def get_default_location():
    """
    기본 위치 반환 (서울시청)
    """
    return {
        'lat': 37.5665,
        'lng': 126.9780,
        'city': '서울',
        'country': '대한민국'
    }


def get_client_ip(request):
    """
    요청에서 클라이언트 IP 주소 추출
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
