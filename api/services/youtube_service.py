"""
YouTube API 서비스 - 개선된 버전
"""
import requests
import os
import random
import logging
from django.core.cache import cache
from django.conf import settings
import hashlib

logger = logging.getLogger(__name__)

def get_youtube_music(workout_type='general'):
    """유튜브 음악 추천 - 개선된 버전"""
    try:
        # 캐시 확인
        cache_key = f"youtube_music_{hashlib.md5(workout_type.encode()).hexdigest()}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        api_key = settings.YOUTUBE_API_KEY
        if not api_key or api_key == 'your_youtube_api_key_here':
            logger.warning("YouTube API key not configured, using default data")
            return get_default_music_data(workout_type)
        
        # 운동 타입별 음악 검색 쿼리
        search_queries = {
            'cardio': 'cardio workout music mix 2024 high energy BPM',
            'cardio_energetic': 'high energy cardio music 140-180 BPM workout',
            'strength': 'gym workout music motivation strength training 2024',
            'strength_powerful': 'heavy metal gym music powerlifting motivation',
            'yoga': 'yoga meditation music relaxing peaceful 2024',
            'yoga_calm': 'deep relaxation yoga music zen meditation',
            'hiit': 'HIIT workout music intense interval training 2024',
            'hiit_intense': 'extreme HIIT music high intensity tabata',
            'running': 'running music 160-180 BPM marathon training 2024',
            'running_energetic': 'sprint running music fast tempo motivation',
            'pilates': 'pilates workout music flow relaxing 2024',
            'dance': 'dance workout music zumba aerobics 2024',
            'cycling': 'cycling spinning music high energy indoor bike',
            'general': 'workout music mix motivation 2024'
        }
        
        # 무드 기반 추가 키워드
        mood_keywords = {
            'energetic': 'high energy upbeat fast tempo',
            'calm': 'relaxing peaceful slow tempo',
            'powerful': 'intense motivation aggressive',
            'focused': 'concentration steady rhythm'
        }
        
        # 쿼리 생성
        base_query = search_queries.get(workout_type, search_queries['general'])
        
        # 무드가 포함된 경우 처리
        if '_' in workout_type:
            exercise, mood = workout_type.split('_', 1)
            if mood in mood_keywords:
                base_query += f" {mood_keywords[mood]}"
        
        youtube_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': base_query,
            'key': api_key,
            'type': 'video',
            'videoCategoryId': '10',  # 음악 카테고리
            'maxResults': 15,
            'order': 'relevance',
            'videoDuration': 'long',  # 20분 이상
            'relevanceLanguage': 'ko'  # 한국어 우선
        }
        
        response = requests.get(youtube_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            videos = []
            
            for item in data.get('items', []):
                video = {
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'][:200] + '...',
                    'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                    'channel': item['snippet']['channelTitle'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'embed_url': f"https://www.youtube.com/embed/{item['id']['videoId']}"
                }
                videos.append(video)
            
            result = {
                'workout_type': workout_type,
                'query': base_query,
                'count': len(videos),
                'videos': videos,
                'items': videos  # 호환성을 위해
            }
            
            # 캐시 저장 (6시간)
            cache.set(cache_key, result, 60 * 60 * 6)
            return result
            
        elif response.status_code == 403:
            # API 할당량 초과
            logger.error("YouTube API quota exceeded")
            return get_default_music_data(workout_type)
        else:
            logger.error(f"YouTube API error: {response.status_code}")
            return get_default_music_data(workout_type)
            
    except Exception as e:
        logger.error(f"YouTube music search error: {str(e)}")
        return get_default_music_data(workout_type)

def get_workout_videos(exercise_type='general', difficulty='beginner'):
    """운동 영상 추천 - 개선된 버전"""
    try:
        # 캐시 확인
        cache_key = f"youtube_videos_{hashlib.md5(f'{exercise_type}_{difficulty}'.encode()).hexdigest()}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        api_key = settings.YOUTUBE_API_KEY
        if not api_key or api_key == 'your_youtube_api_key_here':
            logger.warning("YouTube API key not configured, using default data")
            return get_default_workout_videos(exercise_type, difficulty)
        
        # 난이도별 키워드
        difficulty_keywords = {
            'beginner': '초급 입문자 쉬운 기초',
            'intermediate': '중급 일반',
            'advanced': '고급 상급 전문가'
        }
        
        # 운동 타입별 검색 쿼리
        search_queries = {
            'cardio': f'{difficulty} cardio workout at home 홈트 유산소',
            'strength': f'{difficulty} strength training workout 근력 운동',
            'yoga': f'{difficulty} yoga flow 요가 플로우',
            'hiit': f'{difficulty} HIIT workout 고강도 인터벌',
            'pilates': f'{difficulty} pilates workout 필라테스',
            'stretching': f'{difficulty} stretching routine 스트레칭',
            'abs': f'{difficulty} abs workout 복근 운동',
            'general': f'{difficulty} home workout 홈트레이닝'
        }
        
        query = search_queries.get(exercise_type, search_queries['general'])
        # 한국어 난이도 키워드 추가
        if difficulty in difficulty_keywords:
            query += f" {difficulty_keywords[difficulty]}"
        
        youtube_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'key': api_key,
            'type': 'video',
            'videoCategoryId': '17',  # 스포츠 카테고리
            'maxResults': 12,
            'order': 'relevance',
            'videoDuration': 'medium',  # 4-20분
            'relevanceLanguage': 'ko'
        }
        
        response = requests.get(youtube_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            videos = []
            
            for item in data.get('items', []):
                video = {
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'][:300] + '...',
                    'thumbnail': item['snippet']['thumbnails']['high']['url'],
                    'channel': item['snippet']['channelTitle'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'embed_url': f"https://www.youtube.com/embed/{item['id']['videoId']}",
                    'difficulty': difficulty,
                    'type': exercise_type
                }
                videos.append(video)
            
            result = {
                'exercise_type': exercise_type,
                'difficulty': difficulty,
                'query': query,
                'count': len(videos),
                'videos': videos,
                'items': videos  # 호환성을 위해
            }
            
            # 캐시 저장 (12시간)
            cache.set(cache_key, result, 60 * 60 * 12)
            return result
            
        elif response.status_code == 403:
            logger.error("YouTube API quota exceeded")
            return get_default_workout_videos(exercise_type, difficulty)
        else:
            logger.error(f"YouTube API error: {response.status_code}")
            return get_default_workout_videos(exercise_type, difficulty)
            
    except Exception as e:
        logger.error(f"YouTube workout video search error: {str(e)}")
        return get_default_workout_videos(exercise_type, difficulty)

def get_default_music_data(workout_type):
    """기본 음악 데이터 (YouTube API 사용 불가 시)"""
    default_music = {
        'cardio': {
            'videos': [
                {
                    'id': 'D4Fhgr0aHJA',
                    'title': '최고의 유산소 운동 음악 믹스 2024 🔥 에너지 넘치는 운동 플레이리스트',
                    'channel': 'Workout Music',
                    'thumbnail': 'https://img.youtube.com/vi/D4Fhgr0aHJA/mqdefault.jpg',
                    'url': 'https://www.youtube.com/watch?v=D4Fhgr0aHJA'
                },
                {
                    'id': '7wtfhZwyrcc',
                    'title': 'Best Cardio Music Mix 2024 💪 Gym Training Motivation',
                    'channel': 'Fitness Beats',
                    'thumbnail': 'https://img.youtube.com/vi/7wtfhZwyrcc/mqdefault.jpg',
                    'url': 'https://www.youtube.com/watch?v=7wtfhZwyrcc'
                }
            ]
        },
        'strength': {
            'videos': [
                {
                    'id': 'gJLIiF15wjQ',
                    'title': 'Gym Workout Music 2024 🏋️ Best Training Motivation Mix',
                    'channel': 'Gym Music',
                    'thumbnail': 'https://img.youtube.com/vi/gJLIiF15wjQ/mqdefault.jpg',
                    'url': 'https://www.youtube.com/watch?v=gJLIiF15wjQ'
                }
            ]
        },
        'yoga': {
            'videos': [
                {
                    'id': 'v7AYKMP6rOE',
                    'title': 'Relaxing Yoga Music 🧘 Meditation & Stress Relief',
                    'channel': 'Meditation Relax Music',
                    'thumbnail': 'https://img.youtube.com/vi/v7AYKMP6rOE/mqdefault.jpg',
                    'url': 'https://www.youtube.com/watch?v=v7AYKMP6rOE'
                }
            ]
        },
        'general': {
            'videos': [
                {
                    'id': 'HgzGwKwLmgM',
                    'title': 'Ultimate Workout Music Mix 2024 🎵 Best Gym Songs',
                    'channel': 'Workout Channel',
                    'thumbnail': 'https://img.youtube.com/vi/HgzGwKwLmgM/mqdefault.jpg',
                    'url': 'https://www.youtube.com/watch?v=HgzGwKwLmgM'
                }
            ]
        }
    }
    
    # 운동 타입 매칭
    for key in default_music:
        if key in workout_type.lower():
            result = default_music[key]
            result.update({
                'workout_type': workout_type,
                'count': len(result['videos']),
                'items': result['videos']
            })
            return result
    
    # 기본값
    result = default_music['general']
    result.update({
        'workout_type': workout_type,
        'count': len(result['videos']),
        'items': result['videos']
    })
    return result

def get_default_workout_videos(exercise_type, difficulty):
    """기본 운동 영상 데이터"""
    default_videos = {
        'beginner': {
            'videos': [
                {
                    'id': 'ml6cT4AZdqI',
                    'title': '초보자를 위한 홈트레이닝 | 전신운동 15분 루틴',
                    'channel': '홈트레이닝TV',
                    'thumbnail': 'https://img.youtube.com/vi/ml6cT4AZdqI/hqdefault.jpg',
                    'url': 'https://www.youtube.com/watch?v=ml6cT4AZdqI',
                    'difficulty': 'beginner',
                    'type': exercise_type
                }
            ]
        },
        'intermediate': {
            'videos': [
                {
                    'id': 'UBMk30rjy0o',
                    'title': '중급자 전신 운동 루틴 | 30분 홈트레이닝',
                    'channel': 'Fitness Korea',
                    'thumbnail': 'https://img.youtube.com/vi/UBMk30rjy0o/hqdefault.jpg',
                    'url': 'https://www.youtube.com/watch?v=UBMk30rjy0o',
                    'difficulty': 'intermediate',
                    'type': exercise_type
                }
            ]
        },
        'advanced': {
            'videos': [
                {
                    'id': 'ixkO1DXHGhY',
                    'title': '상급자 HIIT 운동 | 고강도 인터벌 트레이닝',
                    'channel': 'Pro Fitness',
                    'thumbnail': 'https://img.youtube.com/vi/ixkO1DXHGhY/hqdefault.jpg',
                    'url': 'https://www.youtube.com/watch?v=ixkO1DXHGhY',
                    'difficulty': 'advanced',
                    'type': exercise_type
                }
            ]
        }
    }
    
    result = default_videos.get(difficulty, default_videos['beginner'])
    result.update({
        'exercise_type': exercise_type,
        'difficulty': difficulty,
        'count': len(result['videos']),
        'items': result['videos']
    })
    return result
