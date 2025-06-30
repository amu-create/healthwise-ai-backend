from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import hashlib
from django.conf import settings
from django.core.cache import cache
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def get_default_search_results(query):
    """
    YouTube API를 사용할 수 없을 때 반환할 기본 검색 결과
    """
    # 운동 종류별 기본 음악 추천
    workout_music = {
        'running': [
            {'id': 'dQw4w9WgXcQ', 'title': 'Running Motivation Mix 2024', 'channel': 'Workout Music'},
            {'id': 'ZbZSe6N_BXs', 'title': 'Best Running Songs 140-180 BPM', 'channel': 'Fitness Beats'},
            {'id': 'Y2V6yjjPbX0', 'title': 'Epic Running Music Mix', 'channel': 'Sport Music'},
        ],
        'yoga': [
            {'id': 'hlWiI4xVXKY', 'title': 'Relaxing Yoga Music', 'channel': 'Meditation Relax Music'},
            {'id': '1ZYbU82GVz4', 'title': 'Morning Yoga Flow Music', 'channel': 'Yoga Music'},
            {'id': 'lCOF9LN_Zxs', 'title': 'Peaceful Yoga Meditation', 'channel': 'Calm Music'},
        ],
        'gym': [
            {'id': '7wtfhZwyrcc', 'title': 'Gym Workout Music Mix 2024', 'channel': 'Gym Music'},
            {'id': 'gJLIiF15wjQ', 'title': 'Best Gym Training Motivation', 'channel': 'Workout Beats'},
            {'id': 'HgzGwKwLmgM', 'title': 'Heavy Metal Workout Mix', 'channel': 'Metal Gym'},
        ],
        'default': [
            {'id': 'dQw4w9WgXcQ', 'title': 'Workout Motivation Mix', 'channel': 'Fitness Music'},
            {'id': 'ZbZSe6N_BXs', 'title': 'Best Exercise Music 2024', 'channel': 'Workout Channel'},
            {'id': 'Y2V6yjjPbX0', 'title': 'Ultimate Training Playlist', 'channel': 'Sport Music'},
        ]
    }
    
    # 쿼리에서 운동 종류 찾기
    query_lower = query.lower()
    selected_music = workout_music['default']
    
    for workout_type, music_list in workout_music.items():
        if workout_type in query_lower:
            selected_music = music_list
            break
    
    # YouTube API 응답 형식으로 변환
    items = []
    for music in selected_music[:5]:  # 최대 5개
        items.append({
            'id': {'videoId': music['id']},
            'snippet': {
                'title': music['title'],
                'channelTitle': music['channel'],
                'thumbnails': {
                    'default': {'url': f"https://img.youtube.com/vi/{music['id']}/default.jpg"},
                    'medium': {'url': f"https://img.youtube.com/vi/{music['id']}/mqdefault.jpg"},
                    'high': {'url': f"https://img.youtube.com/vi/{music['id']}/hqdefault.jpg"}
                }
            }
        })
    
    return {'items': items}


@csrf_exempt
@require_http_methods(["POST"])
def youtube_search_guest(request):
    """비회원용 YouTube 검색 API"""
    try:
        data = json.loads(request.body)
        query = data.get('query', '')
        max_results = data.get('maxResults', 5)
        
        if not query:
            return JsonResponse({'error': '검색어를 입력해주세요.'}, status=400)
        
        # 캐시 키 생성
        cache_key = f"youtube_search_guest_{hashlib.md5(f'{query}_{max_results}'.encode()).hexdigest()}"
        
        # 캐시 확인
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached YouTube search result for guest query: {query}")
            return JsonResponse(cached_result)
        
        # API 키 가져오기
        api_key = getattr(settings, 'YOUTUBE_API_KEY', '')
        
        # 기본값이거나 비어있으면 환경변수에서 다시 읽기
        if not api_key or api_key == 'your_youtube_api_key_here' or api_key == '':
            # .env 파일에서 직접 읽기 시도
            env_path = Path(settings.BASE_DIR) / '.env'
            load_dotenv(env_path)
            api_key = os.environ.get('YOUTUBE_API_KEY', '')
            
            # 그래도 없으면 .env 파일 직접 파싱
            if not api_key or api_key == 'your_youtube_api_key_here':
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        for line in f:
                            if line.strip().startswith('YOUTUBE_API_KEY='):
                                api_key = line.strip().split('=', 1)[1]
                                break
        
        if not api_key:
            # API 키가 없는 경우 기본 검색 결과 반환
            logger.warning("YouTube API key not configured, returning default results")
            default_results = get_default_search_results(query)
            return JsonResponse(default_results)
        
        # YouTube API 호출
        try:
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'maxResults': max_results,
                'q': query,
                'type': 'video',
                'videoCategoryId': '10',  # 음악 카테고리
                'key': api_key
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 403:
                # 할당량 초과 시 기본 결과 반환
                logger.error(f"YouTube API quota exceeded: {response.text}")
                default_results = get_default_search_results(query)
                return JsonResponse(default_results)
            
            if response.status_code != 200:
                logger.error(f"YouTube API Error: {response.text}")
                # 오류 발생 시 기본 결과 반환
                default_results = get_default_search_results(query)
                return JsonResponse(default_results)
            
            result = response.json()
            
            # 결과를 캐시에 저장 (12시간)
            cache.set(cache_key, result, 60 * 60 * 12)
            logger.info(f"Cached YouTube search result for guest query: {query}")
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.exception("YouTube search error")
            # 오류 발생 시 기본 결과 반환
            default_results = get_default_search_results(query)
            return JsonResponse(default_results)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 요청 형식입니다.'}, status=400)
    except Exception as e:
        logger.error(f"YouTube search error: {str(e)}")
        # 예외 발생 시도 기본 결과 반환
        default_results = get_default_search_results(query)
        return JsonResponse(default_results)
