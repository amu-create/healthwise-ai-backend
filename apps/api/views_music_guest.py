from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.cache import cache
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 비회원의 일일 API 호출 제한
GUEST_API_LIMIT = 10


def check_guest_api_limit(request, api_type):
    """비회원의 API 호출 횟수 확인"""
    # IP 주소 또는 세션 ID로 구분
    guest_id = request.session.get('guest_id')
    if not guest_id:
        # 세션에 guest_id가 없으면 IP 주소 사용
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        guest_id = f"ip_{ip}"
    
    # 캐시 키 생성 (날짜별로 리셋)
    today = datetime.now().strftime('%Y%m%d')
    cache_key = f"guest_api_limit_{guest_id}_{api_type}_{today}"
    
    # 현재 호출 횟수 확인
    current_count = cache.get(cache_key, 0)
    
    if current_count >= GUEST_API_LIMIT:
        return False, current_count
    
    # 호출 횟수 증가
    cache.set(cache_key, current_count + 1, 86400)  # 24시간 후 만료
    
    return True, current_count + 1


@api_view(['POST'])
@permission_classes([AllowAny])
def ai_keywords_guest(request):
    """비회원을 위한 AI 키워드 생성 (제한적)"""
    
    # API 호출 제한 확인
    allowed, count = check_guest_api_limit(request, 'ai_keywords')
    if not allowed:
        return Response({
            'error': '일일 API 호출 제한을 초과했습니다.',
            'message': f'비회원은 하루에 {GUEST_API_LIMIT}회까지만 이용 가능합니다. 더 많은 기능을 이용하려면 회원가입을 해주세요.',
            'daily_limit': GUEST_API_LIMIT,
            'current_count': count
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    data = request.data
    location = data.get('location', '')
    duration = data.get('duration', 30)
    mood = data.get('mood', '중간')
    
    # 기본 키워드 생성 (GPT 호출 없이)
    if '공원' in location or '산' in location:
        keywords = ['자연', '힐링', '산책', '조깅']
    elif '헬스장' in location or '피트니스' in location:
        keywords = ['운동', '헬스', '트레이닝', '다이어트']
    elif '집' in location or '홈' in location:
        keywords = ['홈트', '집에서', '실내운동', '요가']
    else:
        keywords = ['운동', '건강', '활력', '에너지']
    
    # 기분에 따른 키워드 추가
    if mood == '우울함':
        keywords.append('힐링')
        keywords.append('위로')
    elif mood == '신남':
        keywords.append('신나는')
        keywords.append('파워풀')
    elif mood == '차분함':
        keywords.append('명상')
        keywords.append('릴렉스')
    
    return Response({
        'keywords': keywords[:4],  # 최대 4개까지
        'is_guest': True,
        'guest_info': {
            'daily_limit': GUEST_API_LIMIT,
            'remaining': GUEST_API_LIMIT - count,
            'message': f'오늘 {count}/{GUEST_API_LIMIT}회 이용했습니다.'
        }
    }, status=status.HTTP_200_OK)
