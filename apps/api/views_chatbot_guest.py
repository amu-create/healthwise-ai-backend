from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from datetime import datetime
import json
import logging
import openai
from django.conf import settings

logger = logging.getLogger(__name__)

# 비회원 일일 메시지 제한
GUEST_CHATBOT_LIMIT = 5  # 5번으로 변경

def get_guest_id(request):
    """비회원 식별자 생성"""
    guest_id = request.session.get('guest_id')
    if not guest_id:
        # IP 주소 사용
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        guest_id = f"ip_{ip}"
    return guest_id

def check_guest_chatbot_limit(request):
    """비회원 챗봇 사용 횟수 확인"""
    guest_id = get_guest_id(request)
    today = datetime.now().strftime('%Y%m%d')
    cache_key = f"guest_chatbot_{guest_id}_{today}"
    
    current_count = cache.get(cache_key, 0)
    
    if current_count >= GUEST_CHATBOT_LIMIT:
        return False, current_count, 0
    
    remaining = GUEST_CHATBOT_LIMIT - current_count
    return True, current_count, remaining

def increment_guest_chatbot_count(request):
    """비회원 챗봇 사용 횟수 증가"""
    guest_id = get_guest_id(request)
    today = datetime.now().strftime('%Y%m%d')
    cache_key = f"guest_chatbot_{guest_id}_{today}"
    
    current_count = cache.get(cache_key, 0)
    cache.set(cache_key, current_count + 1, 86400)  # 24시간 후 만료
    
    return current_count + 1

@csrf_exempt
@require_http_methods(["GET"])
def guest_chatbot_sessions(request):
    """비회원용 챗봇 세션 목록"""
    return JsonResponse({
        'sessions': [],
        'is_guest': True,
        'message': '비회원은 대화 기록이 저장되지 않습니다.'
    })

@csrf_exempt
@require_http_methods(["GET"])
def guest_chatbot_active_session(request):
    """비회원용 활성 세션 정보"""
    return JsonResponse({
        'session': {
            'id': 'guest-session',
            'name': '게스트 대화',
            'created_at': datetime.now().isoformat(),
            'is_active': True
        },
        'is_guest': True,
        'message': '비회원은 임시 세션을 사용합니다.'
    })

@csrf_exempt
@require_http_methods(["GET"])
def guest_chatbot_status(request):
    """비회원용 챗봇 상태"""
    allowed, count, remaining = check_guest_chatbot_limit(request)
    
    return JsonResponse({
        'status': 'ready' if allowed else 'limit_exceeded',
        'is_guest': True,
        'daily_message_count': count,
        'daily_message_limit': GUEST_CHATBOT_LIMIT,
        'remaining_messages': remaining,
        'message': f'비회원은 하루 {GUEST_CHATBOT_LIMIT}개의 메시지만 보낼 수 있습니다. (남은 횟수: {remaining}회)'
    })

@csrf_exempt
@require_http_methods(["POST"])
def guest_chatbot(request):
    """비회원용 챗봇 대화"""
    try:
        # 사용 횟수 체크
        allowed, count, remaining = check_guest_chatbot_limit(request)
        if not allowed:
            return JsonResponse({
                'error': '일일 메시지 제한을 초과했습니다.',
                'message': f'비회원은 하루에 {GUEST_CHATBOT_LIMIT}회까지만 이용 가능합니다. 더 많은 기능을 이용하려면 회원가입을 해주세요.',
                'daily_limit': GUEST_CHATBOT_LIMIT,
                'current_count': count
            }, status=429)
        
        data = json.loads(request.body)
        message = data.get('message', '')
        
        if not message:
            return JsonResponse({'error': '메시지를 입력해주세요.'}, status=400)
        
        # 사용 횟수 증가
        new_count = increment_guest_chatbot_count(request)
        remaining_after = GUEST_CHATBOT_LIMIT - new_count
        
        # 간단한 AI 응답 생성
        try:
            # OpenAI API 사용
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 건강 관리를 도와주는 친절한 AI 헬스케어 도우미입니다. 사용자가 비회원이라는 점을 고려하여 간단하고 유용한 조언을 제공하되, 전문적인 의료 조언은 하지 마세요."},
                    {"role": "user", "content": message}
                ],
                max_tokens=150,  # 비회원은 짧은 응답
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            # 기본 응답
            ai_response = "죄송합니다. 잠시 후 다시 시도해주세요. 비회원으로 이용 중이시니 제한된 기능만 사용 가능합니다."
        
        return JsonResponse({
            'response': ai_response,
            'is_guest': True,
            'remaining_messages': remaining_after,
            'usage_info': {
                'daily_limit': GUEST_CHATBOT_LIMIT,
                'used_today': new_count,
                'remaining': remaining_after
            },
            'message': f'오늘 {new_count}/{GUEST_CHATBOT_LIMIT}회 사용했습니다.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 요청 형식입니다.'}, status=400)
    except Exception as e:
        logger.error(f"Guest chatbot error: {str(e)}")
        return JsonResponse({'error': '대화 처리 중 오류가 발생했습니다.'}, status=500)
