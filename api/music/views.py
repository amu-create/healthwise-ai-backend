from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.core.cache import cache
from openai import OpenAI
import requests
import hashlib
import logging
import os

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_ai_keywords(request):
    """
    AI를 사용하여 운동과 기분에 맞는 음악 키워드 생성
    """
    data = request.data
    exercise = data.get('exercise')
    mood = data.get('mood')
    
    if not exercise or not mood:
        return Response(
            {'error': 'Both exercise and mood are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 운동 종류를 한글로 변환
    exercise_ko = {
        'running': '달리기',
        'walking': '걷기', 
        'yoga': '요가',
        'strength': '근력 운동',
        'cycling': '자전거'
    }.get(exercise, exercise)
    
    # 기분을 한글로 변환
    mood_ko = {
        'energetic': '활기찬',
        'calm': '차분한',
        'focused': '집중된',
        'relaxed': '편안한',
        'pumped': '흥분된'
    }.get(mood, mood)
    
    prompt = f"""
    {exercise_ko} 운동을 할 때 '{mood_ko}' 기분에 잘 어울리는 음악 키워드를 5개 추천해줘.
    
    - 각 키워드는 유튜브에서 검색했을 때 음악/플레이리스트가 잘 나오도록 구성
    - 장르, BPM, 분위기 등을 고려해서 추천
    - 각 키워드는 한 줄씩, 번호나 설명 없이 키워드만 출력
    """
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        keywords = [line.strip() for line in content.strip().split('\n') if line.strip()]
        
        return Response({'keywords': keywords[:5]})
        
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        # OpenAI API 실패 시 기본 키워드 제공
        default_keywords = get_default_keywords(exercise, mood)
        return Response({'keywords': default_keywords})


def get_default_keywords(exercise, mood):
    """운동과 기분에 따른 기본 키워드"""
    keywords_map = {
        ('running', 'energetic'): ['Upbeat Running Music', '180 BPM Workout Mix', 'Electronic Dance Workout', 'Power Running Playlist', 'High Energy Cardio'],
        ('running', 'calm'): ['Slow Jogging Music', 'Chill Running Playlist', 'Ambient Running Mix', 'Peaceful Cardio Music', 'Zen Running'],
        ('walking', 'energetic'): ['Happy Walking Music', 'Uplifting Walking Mix', 'Pop Walking Playlist', 'Feel Good Walk', 'Energetic Stroll Music'],
        ('walking', 'calm'): ['Relaxing Walking Music', 'Nature Walk Sounds', 'Peaceful Walking Mix', 'Meditation Walk', 'Calm Stroll Playlist'],
        ('yoga', 'calm'): ['Yoga Meditation Music', 'Peaceful Yoga Flow', 'Zen Yoga Playlist', 'Calming Yoga Mix', 'Spiritual Yoga Music'],
        ('yoga', 'focused'): ['Vinyasa Flow Music', 'Concentration Yoga', 'Mindful Yoga Mix', 'Focus Meditation Music', 'Yoga Practice Playlist'],
        ('strength', 'energetic'): ['Gym Motivation Mix', 'Heavy Metal Workout', 'Powerlifting Music', 'Beast Mode Playlist', 'Intense Training Mix'],
        ('strength', 'pumped'): ['Pre-Workout Hype Music', 'Adrenaline Gym Mix', 'Pump Up Playlist', 'Hardcore Training Music', 'Max Rep Motivation'],
        ('cycling', 'energetic'): ['Cycling Cadence Music', 'Spin Class Mix', 'Indoor Cycling Playlist', 'Tour de Music', 'High Tempo Bike Mix'],
        ('cycling', 'focused'): ['Endurance Cycling Music', 'Long Ride Playlist', 'Steady Pace Mix', 'Zone Training Music', 'Cycling Meditation']
    }
    
    # 정확한 매치가 있으면 사용
    if (exercise, mood) in keywords_map:
        return keywords_map[(exercise, mood)]
    
    # 운동 종류만 매치
    for key, value in keywords_map.items():
        if key[0] == exercise:
            return value
    
    # 기본값
    return ['Workout Music Mix', 'Exercise Playlist', 'Training Music', 'Fitness Beats', 'Gym Motivation']


@api_view(['POST'])
@permission_classes([AllowAny])
def youtube_search(request):
    """
    YouTube API 검색 (서버 프록시)
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
        return Response(cached_result)
    
    # YouTube API 키 확인
    api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
    
    if not api_key or api_key == 'your-youtube-api-key-here':
        # API 키가 없으면 기본 결과 반환
        default_results = get_default_search_results(query)
        return Response(default_results)
    
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'maxResults': max_results,
            'q': query,
            'type': 'video',
            'videoCategoryId': '10',  # Music category
            'key': api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            result = response.json()
            # 캐시에 저장 (12시간)
            cache.set(cache_key, result, 60 * 60 * 12)
            return Response(result)
        else:
            logger.error(f"YouTube API error: {response.status_code}")
            # API 오류 시 기본 결과 반환
            default_results = get_default_search_results(query)
            return Response(default_results)
            
    except Exception as e:
        logger.exception("YouTube search error")
        # 예외 발생 시 기본 결과 반환
        default_results = get_default_search_results(query)
        return Response(default_results)


def get_default_search_results(query):
    """YouTube API 없이 기본 검색 결과 반환"""
    # 쿼리에 따라 다른 기본 비디오 제공
    default_videos = {
        'running': [
            {'id': 'gJLIiF15wjQ', 'title': 'Best Running Music Mix 2024 🏃 Jogging Music', 'channel': 'Workout Music Service'},
            {'id': 'BcKlRQuOzeY', 'title': '1 Hour Running Music Mix | Best Running Motivation Music 2024', 'channel': 'Music for Running'},
            {'id': 'HgzGwKwLmgM', 'title': 'Running Music 2024 | Best Songs for Running', 'channel': 'EDM Workout Music'},
        ],
        'yoga': [
            {'id': 'v7AYKMP6rOE', 'title': 'Relaxing Yoga Music ● Calming Music ● Stress Relief Music', 'channel': 'Yellow Brick Cinema'},
            {'id': 'hlWiI4xVXKY', 'title': '1 Hour Yoga Music for Your Yoga Practice', 'channel': 'Meditation Relax Music'},
            {'id': 'COp7BR_Dvps', 'title': 'Yoga Music, Relaxing Music, Calming Music', 'channel': 'Body Mind Zone'},
        ],
        'workout': [
            {'id': '7wtfhZwyrcc', 'title': 'Best Workout Music Mix 2024 💪 Gym Motivation Music', 'channel': 'Workout Music Source'},
            {'id': 'qWf-FPFmVw0', 'title': '1 HOUR Workout Music 2024', 'channel': 'NCS Workout'},
            {'id': '04854XqcfCY', 'title': 'Gym Music 2024 - Best Deep House & EDM Workout Music', 'channel': 'Emu Music'},
        ]
    }
    
    # 쿼리에서 키워드 찾기
    query_lower = query.lower()
    selected_videos = default_videos.get('workout', [])  # 기본값
    
    for keyword, videos in default_videos.items():
        if keyword in query_lower:
            selected_videos = videos
            break
    
    # YouTube API 응답 형식으로 변환
    items = []
    for video in selected_videos:
        items.append({
            'id': {'videoId': video['id']},
            'snippet': {
                'title': video['title'],
                'channelTitle': video['channel'],
                'thumbnails': {
                    'default': {'url': f"https://img.youtube.com/vi/{video['id']}/default.jpg"},
                    'medium': {'url': f"https://img.youtube.com/vi/{video['id']}/mqdefault.jpg"},
                    'high': {'url': f"https://img.youtube.com/vi/{video['id']}/hqdefault.jpg"}
                }
            }
        })
    
    return {'items': items}


@api_view(['POST'])
@permission_classes([AllowAny])
def save_feedback(request):
    """음악 피드백 저장 (현재는 로그만)"""
    data = request.data
    feedback = data.get('feedback')
    songs_played = data.get('songs_played', [])
    
    logger.info(f"Music feedback: {feedback}, Songs: {songs_played}")
    
    return Response({'status': 'success'})
