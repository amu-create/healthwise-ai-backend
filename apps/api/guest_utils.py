import uuid
from django.core.cache import cache
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 비회원의 일일 API 호출 제한
GUEST_API_LIMITS = {
    'AI_WORKOUT': 3,
    'CHATBOT': 5,
    'MUSIC_AI': 3,
}

def get_or_create_guest_id(request):
    """게스트 ID를 가져오거나 생성"""
    # 1. 헤더에서 게스트 ID 확인
    guest_id = request.headers.get('X-Guest-ID')
    
    # 2. 세션에서 게스트 ID 확인
    if not guest_id:
        guest_id = request.session.get('guest_id')
    
    # 3. 새로 생성
    if not guest_id:
        guest_id = str(uuid.uuid4())
        request.session['guest_id'] = guest_id
        request.session['is_guest'] = True
        request.session.set_expiry(60 * 60 * 24 * 7)  # 7일
        logger.info(f"New guest ID created: {guest_id}")
    
    return guest_id

def check_guest_api_limit(request, feature_key):
    """비회원의 API 호출 횟수 확인"""
    # 게스트 ID 가져오기
    guest_id = get_or_create_guest_id(request)
    
    # 기능별 제한 확인
    limit = GUEST_API_LIMITS.get(feature_key, 3)
    
    # 캐시 키 생성 (날짜별로 리셋)
    today = datetime.now().strftime('%Y%m%d')
    cache_key = f"guest_api_limit_{feature_key}_{guest_id}_{today}"
    
    # 현재 호출 횟수 확인
    current_count = cache.get(cache_key, 0)
    
    logger.info(f"Guest API check - ID: {guest_id}, Feature: {feature_key}, Count: {current_count}/{limit}")
    
    if current_count >= limit:
        return False, current_count, limit, guest_id
    
    # 호출 횟수 증가
    cache.set(cache_key, current_count + 1, 86400)  # 24시간 후 만료
    
    return True, current_count + 1, limit, guest_id

def get_guest_usage_info(request):
    """게스트 사용 정보 조회"""
    guest_id = get_or_create_guest_id(request)
    today = datetime.now().strftime('%Y%m%d')
    
    usage_info = {}
    for feature_key, limit in GUEST_API_LIMITS.items():
        cache_key = f"guest_api_limit_{feature_key}_{guest_id}_{today}"
        current_count = cache.get(cache_key, 0)
        usage_info[feature_key] = {
            'used': current_count,
            'limit': limit,
            'remaining': max(0, limit - current_count)
        }
    
    return usage_info, guest_id

def reset_guest_usage(request, feature_key=None):
    """게스트 사용 횟수 초기화 (테스트용)"""
    guest_id = get_or_create_guest_id(request)
    today = datetime.now().strftime('%Y%m%d')
    
    if feature_key:
        # 특정 기능만 초기화
        cache_key = f"guest_api_limit_{feature_key}_{guest_id}_{today}"
        cache.delete(cache_key)
        logger.info(f"Reset guest usage - ID: {guest_id}, Feature: {feature_key}")
    else:
        # 모든 기능 초기화
        for feature in GUEST_API_LIMITS.keys():
            cache_key = f"guest_api_limit_{feature}_{guest_id}_{today}"
            cache.delete(cache_key)
        logger.info(f"Reset all guest usage - ID: {guest_id}")
    
    return True
