import requests
import os
import random

def get_youtube_music(workout_type='general'):
    """유튜브 음악 추천"""
    try:
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            return {'error': 'YouTube API key not configured'}
        
        search_queries = {
            'cardio': 'workout music cardio energetic',
            'strength': 'gym music motivation strength training',
            'yoga': 'yoga music relaxing peaceful',
            'hiit': 'hiit workout music high energy',
            'general': 'workout music motivation'
        }
        
        query = search_queries.get(workout_type, search_queries['general'])
        
        youtube_url = f"https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'key': api_key,
            'type': 'video',
            'videoCategoryId': '10',
            'maxResults': 10,
            'order': 'relevance'
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
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                }
                videos.append(video)
            
            return {
                'workout_type': workout_type,
                'count': len(videos),
                'videos': videos
            }
        else:
            return {'error': 'Failed to fetch YouTube data'}
            
    except Exception as e:
        return {'error': f'YouTube API error: {str(e)}'}

def get_workout_videos(exercise_type='general', difficulty='beginner'):
    """운동 영상 추천"""
    try:
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            return {'error': 'YouTube API key not configured'}
        
        search_queries = {
            'cardio': f'{difficulty} cardio workout at home',
            'strength': f'{difficulty} strength training workout',
            'yoga': f'{difficulty} yoga flow',
            'hiit': f'{difficulty} hiit workout',
            'general': f'{difficulty} home workout'
        }
        
        query = search_queries.get(exercise_type, search_queries['general'])
        
        youtube_url = f"https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'key': api_key,
            'type': 'video',
            'videoCategoryId': '17',
            'maxResults': 12,
            'order': 'relevance'
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
                    'embed_url': f"https://www.youtube.com/embed/{item['id']['videoId']}"
                }
                videos.append(video)
            
            return {
                'exercise_type': exercise_type,
                'difficulty': difficulty,
                'count': len(videos),
                'videos': videos
            }
        else:
            return {'error': 'Failed to fetch workout videos'}
            
    except Exception as e:
        return {'error': f'YouTube API error: {str(e)}'}
