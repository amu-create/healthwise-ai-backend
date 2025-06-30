import os
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import requests
from datetime import datetime
import logging
from django.utils import translation

logger = logging.getLogger(__name__)

# YouTube API 설정
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_API_URL = 'https://www.googleapis.com/youtube/v3/search'

# 운동 카테고리별 검색 키워드 (다국어)
EXERCISE_KEYWORDS = {
    'ko': {
        'all': '운동 홈트레이닝 workout',
        'cardio': '유산소 운동 홈트 카디오 cardio workout',
        'strength': '근력 운동 홈트 웨이트 strength training',
        'yoga': '요가 홈트 스트레칭 yoga',
        'pilates': '필라테스 홈트 코어 pilates',
        'hiit': 'HIIT 고강도 인터벌 트레이닝 타바타',
        'stretching': '스트레칭 유연성 운동 stretching',
    },
    'en': {
        'all': 'home workout exercise fitness',
        'cardio': 'cardio workout aerobic exercise',
        'strength': 'strength training weight lifting muscle building',
        'yoga': 'yoga workout flexibility stretching',
        'pilates': 'pilates core workout',
        'hiit': 'HIIT high intensity interval training tabata',
        'stretching': 'stretching flexibility exercise',
    },
    'es': {
        'all': 'ejercicio entrenamiento en casa fitness',
        'cardio': 'cardio ejercicio aeróbico',
        'strength': 'entrenamiento de fuerza pesas',
        'yoga': 'yoga estiramiento flexibilidad',
        'pilates': 'pilates ejercicio core',
        'hiit': 'HIIT entrenamiento intervalos alta intensidad',
        'stretching': 'estiramiento flexibilidad ejercicio',
    }
}

# 난이도별 검색 키워드 (다국어)
DIFFICULTY_KEYWORDS = {
    'ko': {
        'beginner': '초보자 입문 쉬운 beginner',
        'intermediate': '중급 intermediate',
        'advanced': '고급 상급 advanced',
    },
    'en': {
        'beginner': 'beginner easy basic simple',
        'intermediate': 'intermediate moderate',
        'advanced': 'advanced expert hard difficult',
    },
    'es': {
        'beginner': 'principiante fácil básico',
        'intermediate': 'intermedio moderado',
        'advanced': 'avanzado experto difícil',
    }
}

# 언어별 지역 코드
REGION_CODES = {
    'ko': 'KR',
    'en': 'US',
    'es': 'ES'
}

@require_http_methods(['GET'])
def workout_videos(request):
    """
    운동 영상 목록 조회
    """
    try:
        # 쿼리 파라미터 가져오기
        category = request.GET.get('category', 'all')
        difficulty = request.GET.get('difficulty', '')
        search = request.GET.get('search', '')
        max_results = int(request.GET.get('maxResults', 12))
        
        # YouTube API 키 확인
        if not YOUTUBE_API_KEY:
            logger.error("YouTube API key not found")
            # 개발 환경에서는 더미 데이터 반환
            return JsonResponse({
                'items': get_dummy_videos(category, difficulty, search),
                'total': 12,
                'category': category,
                'difficulty': difficulty
            })
        
        # 현재 언어 가져오기 (Accept-Language 헤더 또는 Django 설정)
        current_language = request.headers.get('Accept-Language', 'en')[:2]
        if current_language not in ['ko', 'en', 'es']:
            current_language = translation.get_language()[:2]  # Django 설정 사용
            if current_language not in ['ko', 'en', 'es']:
                current_language = 'en'  # 기본값
        
        # 언어별 키워드 가져오기
        exercise_keywords = EXERCISE_KEYWORDS.get(current_language, EXERCISE_KEYWORDS['en'])
        difficulty_keywords = DIFFICULTY_KEYWORDS.get(current_language, DIFFICULTY_KEYWORDS['en'])
        
        # 검색 쿼리 구성 - 사용자 검색어가 있으면 그것만 사용
        if search:
            # 사용자 검색어 사용
            search_query = search
        else:
            # 검색어가 없을 때만 카테고리/난이도 사용
            query_parts = []
            if category in exercise_keywords:
                query_parts.append(exercise_keywords[category])
            if difficulty in difficulty_keywords:
                query_parts.append(difficulty_keywords[difficulty])
            search_query = ' '.join(query_parts) if query_parts else exercise_keywords.get('all', 'workout')
        
        # YouTube API 호출
        params = {
            'part': 'snippet',
            'q': search_query,
            'type': 'video',
            'videoCategoryId': '17',  # Sports 카테고리
            'videoEmbeddable': 'true',
            'maxResults': max_results,
            'key': YOUTUBE_API_KEY,
            'regionCode': REGION_CODES.get(current_language, 'US'),
            'relevanceLanguage': current_language,
            'order': 'relevance',
            'videoDuration': 'medium',  # 4-20분 영상
            'videoDefinition': 'high',  # HD 영상만
        }
        
        response = requests.get(YOUTUBE_API_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # 응답 데이터 가공
            videos = []
            for item in data.get('items', []):
                snippet = item['snippet']
                video = {
                    'id': item['id']['videoId'],
                    'title': snippet['title'],
                    'thumbnail': snippet['thumbnails']['medium']['url'],
                    'channelTitle': snippet['channelTitle'],
                    'description': snippet['description'][:200] + '...' if len(snippet['description']) > 200 else snippet['description'],
                    'publishedAt': snippet['publishedAt'],
                    'category': category,
                    'difficulty': difficulty
                }
                videos.append(video)
            
            return JsonResponse({
                'items': videos,
                'total': len(videos),
                'category': category,
                'difficulty': difficulty,
                'nextPageToken': data.get('nextPageToken')
            })
        else:
            logger.error(f"YouTube API error: {response.status_code}")
            # API 오류 시 더미 데이터 반환
            return JsonResponse({
                'items': get_dummy_videos(category, difficulty, search),
                'total': 12,
                'category': category,
                'difficulty': difficulty
            })
            
    except Exception as e:
        logger.error(f"Error in workout_videos: {str(e)}")
        # 오류 발생 시 더미 데이터 반환
        return JsonResponse({
            'items': get_dummy_videos(category, difficulty, search),
            'total': 12,
            'category': category,
            'difficulty': difficulty
        })

def get_dummy_videos(category='all', difficulty='', search=''):
    """
    개발/테스트용 더미 비디오 데이터
    """
    base_videos = [
        {
            'id': 'dQw4w9WgXcQ',
            'title': '전신 홈트레이닝 20분 루틴',
            'thumbnail': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg',
            'channelTitle': '홈트레이닝 채널',
            'description': '집에서 할 수 있는 전신 운동 루틴입니다. 준비물 없이 맨몸으로 할 수 있어요.',
            'publishedAt': '2024-01-15T10:00:00Z',
            'category': 'all',
            'difficulty': 'beginner'
        },
        {
            'id': 'ML3vcaIr9Iw',
            'title': '15분 고강도 HIIT 운동',
            'thumbnail': 'https://i.ytimg.com/vi/ML3vcaIr9Iw/mqdefault.jpg',
            'channelTitle': 'HIIT 마스터',
            'description': '짧은 시간에 최대 효과! 15분 고강도 인터벌 트레이닝',
            'publishedAt': '2024-01-14T09:00:00Z',
            'category': 'hiit',
            'difficulty': 'intermediate'
        },
        {
            'id': '1we3bh9TtNQ',
            'title': '초보자를 위한 요가 30분',
            'thumbnail': 'https://i.ytimg.com/vi/1we3bh9TtNQ/mqdefault.jpg',
            'channelTitle': '요가 라이프',
            'description': '요가 입문자를 위한 기초 동작 30분 루틴',
            'publishedAt': '2024-01-13T08:00:00Z',
            'category': 'yoga',
            'difficulty': 'beginner'
        },
        {
            'id': 'gJscrxxR_dQ',
            'title': '필라테스 코어 강화 운동',
            'thumbnail': 'https://i.ytimg.com/vi/gJscrxxR_dQ/mqdefault.jpg',
            'channelTitle': '필라테스 스튜디오',
            'description': '복부와 코어를 강화하는 필라테스 운동',
            'publishedAt': '2024-01-12T07:00:00Z',
            'category': 'pilates',
            'difficulty': 'intermediate'
        },
        {
            'id': 'Zq5EO3a4OGI',
            'title': '유산소 운동 30분 - 체지방 태우기',
            'thumbnail': 'https://i.ytimg.com/vi/Zq5EO3a4OGI/mqdefault.jpg',
            'channelTitle': '카디오 트레이닝',
            'description': '체지방 감소를 위한 효과적인 유산소 운동',
            'publishedAt': '2024-01-11T06:00:00Z',
            'category': 'cardio',
            'difficulty': 'intermediate'
        },
        {
            'id': 'xqvCmoLULNY',
            'title': '근력운동 홈트 - 덤벨 운동법',
            'thumbnail': 'https://i.ytimg.com/vi/xqvCmoLULNY/mqdefault.jpg',
            'channelTitle': '머슬 홈트',
            'description': '집에서 덤벨로 하는 효과적인 근력 운동',
            'publishedAt': '2024-01-10T05:00:00Z',
            'category': 'strength',
            'difficulty': 'advanced'
        },
        {
            'id': 'v7AYKMP6rOE',
            'title': '아침 스트레칭 10분',
            'thumbnail': 'https://i.ytimg.com/vi/v7AYKMP6rOE/mqdefault.jpg',
            'channelTitle': '스트레칭 가이드',
            'description': '하루를 시작하는 활력 스트레칭',
            'publishedAt': '2024-01-09T04:00:00Z',
            'category': 'stretching',
            'difficulty': 'beginner'
        },
        {
            'id': 'cbKkB73AzYk',
            'title': '타바타 4분 전신운동',
            'thumbnail': 'https://i.ytimg.com/vi/cbKkB73AzYk/mqdefault.jpg',
            'channelTitle': '타바타 마스터',
            'description': '4분만에 끝내는 초고강도 전신 운동',
            'publishedAt': '2024-01-08T03:00:00Z',
            'category': 'hiit',
            'difficulty': 'advanced'
        },
        {
            'id': 'UBMk30rjy0o',
            'title': '저녁 요가 - 숙면을 위한 요가',
            'thumbnail': 'https://i.ytimg.com/vi/UBMk30rjy0o/mqdefault.jpg',
            'channelTitle': '요가 힐링',
            'description': '하루의 피로를 푸는 저녁 요가 루틴',
            'publishedAt': '2024-01-07T02:00:00Z',
            'category': 'yoga',
            'difficulty': 'beginner'
        },
        {
            'id': '9bZkp7q19f0',
            'title': '복근 운동 15분 - 식스팩 만들기',
            'thumbnail': 'https://i.ytimg.com/vi/9bZkp7q19f0/mqdefault.jpg',
            'channelTitle': '복근 트레이닝',
            'description': '매일 15분 투자로 만드는 탄탄한 복근',
            'publishedAt': '2024-01-06T01:00:00Z',
            'category': 'strength',
            'difficulty': 'intermediate'
        },
        {
            'id': 'kJQP7kiw5Fk',
            'title': '전신 카디오 댄스 운동',
            'thumbnail': 'https://i.ytimg.com/vi/kJQP7kiw5Fk/mqdefault.jpg',
            'channelTitle': '댄스 피트니스',
            'description': '신나는 음악과 함께하는 카디오 댄스',
            'publishedAt': '2024-01-05T00:00:00Z',
            'category': 'cardio',
            'difficulty': 'beginner'
        },
        {
            'id': 'RgKAFK5djSk',
            'title': '필라테스 매트 운동 25분',
            'thumbnail': 'https://i.ytimg.com/vi/RgKAFK5djSk/mqdefault.jpg',
            'channelTitle': '홈 필라테스',
            'description': '매트만 있으면 OK! 집에서 하는 필라테스',
            'publishedAt': '2024-01-04T23:00:00Z',
            'category': 'pilates',
            'difficulty': 'intermediate'
        }
    ]
    
    # 카테고리 필터링
    if category != 'all':
        base_videos = [v for v in base_videos if v['category'] == category]
    
    # 난이도 필터링
    if difficulty:
        base_videos = [v for v in base_videos if v['difficulty'] == difficulty]
    
    # 검색어 필터링
    if search:
        search_lower = search.lower()
        base_videos = [v for v in base_videos if search_lower in v['title'].lower() or search_lower in v['description'].lower()]
    
    return base_videos
