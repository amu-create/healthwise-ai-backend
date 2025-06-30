from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from openai import OpenAI
import json
import os
import requests
import hashlib
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_ai_keywords(request):
    """
    Get AI-generated music keywords based on exercise and mood
    """
    data = request.data
    exercise = data.get('exercise')
    mood = data.get('mood')
    
    if not exercise or not mood:
        return Response(
            {'error': 'Both exercise and mood are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    prompt = f"""
    {exercise} 운동을 할 때 '{mood}' 기분에 잘 어울리는 유튜브 내 '음악 전용 플레이리스트'나 '음악 믹스 영상' 키워드를 5개 추천해줘.

    - 각 키워드는 실제 유튜브에서 검색했을 때 음악 콘텐츠(노래, 연속재생, 믹스, 플레이리스트)만 뜨도록 구성해줘.
    - 의미 없는 단어 없이 명확한 검색어만 추천해줘 (예: "K-pop workout mix", "relaxing yoga playlist").
    - 음악 외 콘텐츠(토크, 브이로그, 다큐멘터리 등)가 포함되지 않도록 주의해줘.
    - 출력은 줄바꿈(\n)으로 구분된 키워드 5개만 반환해줘. 설명은 포함하지 마.
    """
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.choices[0].message.content
        keywords = [line.strip("123.-• ").strip() for line in content.split('\n') if line.strip()]
        
        # Save user preference
        from apps.api.map.models import MusicPreference
        preference, created = MusicPreference.objects.get_or_create(
            user=request.user
        )
        
        # Update workout-specific preferences
        if not preference.workout_music_preferences:
            preference.workout_music_preferences = {}
        
        preference.workout_music_preferences[exercise] = {
            'mood': mood,
            'keywords': keywords,
            'last_updated': timezone.now().isoformat()
        }
        
        # Update mood preferences
        if not preference.mood_preferences:
            preference.mood_preferences = {}
        
        if mood not in preference.mood_preferences:
            preference.mood_preferences[mood] = []
        
        preference.mood_preferences[mood].extend(keywords)
        # Remove duplicates
        preference.mood_preferences[mood] = list(set(preference.mood_preferences[mood]))
        
        preference.save()
        
        return Response({'keywords': keywords})
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_youtube_api_key(request):
    """
    Get YouTube API key for frontend
    """
    # API 키는 서버에서만 사용하도록 변경
    # 프론트엔드에서는 프록시 API를 사용
    return Response({
        'message': 'Please use the proxy APIs for YouTube searches',
        'endpoints': {
            'search': '/api/music/youtube-search/',
            'popular': '/api/music/popular-tracks/'
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_playlist_feedback(request):
    """
    Save user feedback on music playlist
    """
    data = request.data
    workout_id = data.get('workout_id')
    feedback = data.get('feedback')
    songs_played = data.get('songs_played', [])
    
    try:
        from apps.api.map.models import WorkoutRecord, WorkoutMusic
        workout = WorkoutRecord.objects.get(id=workout_id, user=request.user)
        
        workout_music, created = WorkoutMusic.objects.update_or_create(
            workout_record=workout,
            defaults={
                'feedback': feedback,
                'songs_played': songs_played
            }
        )
        
        return Response({'status': 'success'})
        
    except WorkoutRecord.DoesNotExist:
        return Response(
            {'error': 'Workout not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def youtube_search(request):
    """
    YouTube API 검색을 서버에서 처리 (CORS 문제 해결 + 캐싱)
    """
    query = request.data.get('query')
    max_results = request.data.get('maxResults', 5)
    
    if not query:
        return Response(
            {'error': 'Query is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 캐시 키 생성
    cache_key = f"youtube_search_{hashlib.md5(f'{query}_{max_results}'.encode()).hexdigest()}"
    
    # 캐시 확인
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"Returning cached YouTube search result for query: {query}")
        return Response(cached_result)
    
    # API 키 가져오기
    api_key = settings.YOUTUBE_API_KEY
    
    # 기본값이거나 비어있으면 환경변수에서 다시 읽기
    if not api_key or api_key == 'your_youtube_api_key_here' or api_key == '':
        # .env 파일에서 직접 읽기 시도
        from pathlib import Path
        from dotenv import load_dotenv
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
        return Response(default_results)
    
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        # 운동 관련 키워드 추가
        if 'workout' not in query.lower() and 'exercise' not in query.lower() and 'fitness' not in query.lower():
            query = f"{query} workout music mix"
        
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
            return Response(default_results)
        
        if response.status_code != 200:
            logger.error(f"YouTube API Error: {response.text}")
            return Response(
                {'error': f'YouTube API error: {response.status_code}', 'details': response.text},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        result = response.json()
        
        # 결과를 캐시에 저장 (12시간)
        cache.set(cache_key, result, 60 * 60 * 12)
        logger.info(f"Cached YouTube search result for query: {query}")
        
        return Response(result)
        
    except Exception as e:
        logger.exception("YouTube search error")
        # 오류 발생 시 기본 결과 반환
        default_results = get_default_search_results(query)
        return Response(default_results)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_popular_tracks(request):
    """
    인기 트랙 가져오기 (YouTube API 프록시 + 캐싱)
    """
    playlist_id = request.GET.get('playlistId', 'PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI')
    
    # 캐시 키 생성
    cache_key = f"youtube_popular_{playlist_id}"
    
    # 캐시 확인
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"Returning cached popular tracks for playlist: {playlist_id}")
        return Response(cached_result)
    
    # API 키 가져오기
    api_key = settings.YOUTUBE_API_KEY
    
    # 기본값이거나 비어있으면 환경변수에서 다시 읽기
    if not api_key or api_key == 'your_youtube_api_key_here' or api_key == '':
        # .env 파일에서 직접 읽기 시도
        from pathlib import Path
        from dotenv import load_dotenv
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
        # API 키가 없는 경우 기본 인기 트랙 반환
        logger.warning("YouTube API key not configured, returning default popular tracks")
        default_tracks = get_default_popular_tracks()
        return Response(default_tracks)
    
    try:
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {
            'part': 'snippet',
            'maxResults': 14,
            'playlistId': playlist_id,
            'key': api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 403:
            # 할당량 초과 시 기본 결과 반환
            logger.error(f"YouTube API quota exceeded: {response.text}")
            default_tracks = get_default_popular_tracks()
            return Response(default_tracks)
        
        if response.status_code != 200:
            logger.error(f"YouTube API Error: {response.text}")
            return Response(
                {'error': f'YouTube API error: {response.status_code}', 'details': response.text},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        result = response.json()
        
        # 결과를 캐시에 저장 (24시간)
        cache.set(cache_key, result, 60 * 60 * 24)
        logger.info(f"Cached popular tracks for playlist: {playlist_id}")
        
        return Response(result)
        
    except Exception as e:
        logger.exception("Get popular tracks error")
        # 오류 발생 시 기본 결과 반환
        default_tracks = get_default_popular_tracks()
        return Response(default_tracks)


def get_default_search_results(query):
    """
    YouTube API를 사용할 수 없을 때 반환할 기본 검색 결과
    """
    # 운동 종류별 기본 음악 추천
    workout_music = {
        'running': [
            {'id': 'gJLIiF15wjQ', 'title': 'Running Motivation Mix 2024', 'channel': 'Workout Music'},
            {'id': 'HgzGwKwLmgM', 'title': 'Best Running Songs 140-180 BPM', 'channel': 'Fitness Beats'},
            {'id': '7wtfhZwyrcc', 'title': 'Epic Running Music Mix', 'channel': 'Sport Music'},
        ],
        'yoga': [
            {'id': 'v7AYKMP6rOE', 'title': 'Relaxing Yoga Music', 'channel': 'Meditation Relax Music'},
            {'id': 'UBMk30rjy0o', 'title': 'Morning Yoga Flow Music', 'channel': 'Yoga Music'},
            {'id': 'xqvCmoLULNY', 'title': 'Peaceful Yoga Meditation', 'channel': 'Calm Music'},
        ],
        'gym': [
            {'id': '7wtfhZwyrcc', 'title': 'Gym Workout Music Mix 2024', 'channel': 'Gym Music'},
            {'id': 'gJLIiF15wjQ', 'title': 'Best Gym Training Motivation', 'channel': 'Workout Beats'},
            {'id': 'HgzGwKwLmgM', 'title': 'Heavy Metal Workout Mix', 'channel': 'Metal Gym'},
        ],
        'default': [
            {'id': 'gJLIiF15wjQ', 'title': 'Workout Motivation Mix', 'channel': 'Fitness Music'},
            {'id': '7wtfhZwyrcc', 'title': 'Best Exercise Music 2024', 'channel': 'Workout Channel'},
            {'id': 'HgzGwKwLmgM', 'title': 'Ultimate Training Playlist', 'channel': 'Sport Music'},
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


def get_default_popular_tracks():
    """
    YouTube API를 사용할 수 없을 때 반환할 기본 인기 트랙
    """
    popular_tracks = [
        {'id': 'JGwWNGJdvx8', 'title': 'Shape of You - Ed Sheeran', 'channel': 'Ed Sheeran'},
        {'id': 'kJQP7kiw5Fk', 'title': 'Despacito - Luis Fonsi', 'channel': 'Luis Fonsi'},
        {'id': 'RgKAFK5djSk', 'title': 'See You Again - Wiz Khalifa', 'channel': 'Wiz Khalifa'},
        {'id': 'OPf0YbXqDm0', 'title': 'Uptown Funk - Mark Ronson', 'channel': 'Mark Ronson'},
        {'id': '9bZkp7q19f0', 'title': 'Gangnam Style - PSY', 'channel': 'officialpsy'},
        {'id': 'fRh_vgS2dFE', 'title': 'Sorry - Justin Bieber', 'channel': 'Justin Bieber'},
        {'id': 'CevxZvSJLk8', 'title': 'Roar - Katy Perry', 'channel': 'Katy Perry'},
        {'id': 'hT_nvWreIhg', 'title': 'Counting Stars - OneRepublic', 'channel': 'OneRepublic'},
        {'id': 'KQ6zr6kCPj8', 'title': 'Party Rock Anthem - LMFAO', 'channel': 'LMFAO'},
        {'id': 'LjhCEhWiKXk', 'title': 'Let It Go - Idina Menzel', 'channel': 'DisneyMusicVEVO'},
    ]
    
    # YouTube API 응답 형식으로 변환
    items = []
    for track in popular_tracks:
        items.append({
            'snippet': {
                'resourceId': {'videoId': track['id']},
                'title': track['title'],
                'channelTitle': track['channel'],
                'thumbnails': {
                    'default': {'url': f"https://img.youtube.com/vi/{track['id']}/default.jpg"},
                    'medium': {'url': f"https://img.youtube.com/vi/{track['id']}/mqdefault.jpg"},
                    'high': {'url': f"https://img.youtube.com/vi/{track['id']}/hqdefault.jpg"}
                }
            }
        })
    
    return {'items': items}
