from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import json
from datetime import datetime, timedelta
import random

# 서비스 모듈 import
from .services.data import HEALTH_OPTIONS, EXERCISE_DATA, ROUTINE_DATA
from .services.youtube_service import get_youtube_music, get_workout_videos
from .services.nutrition_service import analyze_food_simple, get_nutrition_mock_data
from .services.social_service import get_social_posts, create_post, like_post_action
from .services.health_consultation import get_health_consultation
from .models import UserProfile

# 기존 기본 API들
@api_view(['GET'])
def test_api(request):
    return Response({'message': 'API is working!', 'method': request.method})

@api_view(['GET'])
def guest_profile(request):
    return Response({
        'id': 'guest-123',
        'username': 'guest',
        'email': 'guest@example.com',
        'is_guest': True,
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def auth_csrf(request):
    return Response({'csrfToken': get_token(request)})

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def auth_login(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = json.loads(request.body) if request.body else {}
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                }
            })
        else:
            return Response({
                'success': False,
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'OPTIONS'])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    logout(request)
    return Response({'success': True})

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def auth_register(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = json.loads(request.body) if request.body else {}
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # 추가 프로필 정보
        birth_date = data.get('birth_date')
        gender = data.get('gender')
        height = data.get('height')
        weight = data.get('weight')
        diseases = data.get('diseases', [])
        health_conditions = data.get('health_conditions', [])
        allergies = data.get('allergies', [])
        fitness_level = data.get('fitness_level', 'beginner')
        
        if not username or not email or not password:
            return Response({
                'success': False,
                'error': 'Username, email, and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({
                'success': False,
                'error': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'error': 'Email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 사용자 생성
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # 프로필 생성
        profile_data = {
            'user': user,
            'fitness_level': fitness_level,
            'diseases': diseases,
            'health_conditions': health_conditions,
            'allergies': allergies,
        }
        
        if birth_date:
            profile_data['birth_date'] = birth_date
        if gender:
            profile_data['gender'] = gender
        if height:
            profile_data['height'] = float(height)
        if weight:
            profile_data['weight'] = float(weight)
            
        UserProfile.objects.create(**profile_data)
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

# 건강 선택지 API
@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def health_options(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return Response(HEALTH_OPTIONS)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def api_health(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return Response({
        'status': 'healthy',
        'service': 'api',
        'version': '1.0.0'
    })

# Guest endpoints for dashboard
@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def guest_fitness_profile(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    return Response({
        'birth_date': '1990-01-01',  # 예시 생년월일
        'height': 175,
        'weight': 70,
        'bmi': 22.9,
        'body_fat_percentage': 18.5,
        'muscle_mass': 57.0,
        'fitness_level': 'intermediate',
        'health_score': 82,
        'last_updated': datetime.now().isoformat()
    })

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def guest_daily_nutrition(request, date):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    nutrition_data = get_nutrition_mock_data(date)
    return Response(nutrition_data)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def guest_nutrition_statistics(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    start_date = request.GET.get('start_date', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    stats = {
        'period': f'{start_date} to {end_date}',
        'average_daily_calories': random.randint(1900, 2100),
        'total_calories': random.randint(13000, 15000),
        'average_nutrients': {
            'protein': random.randint(70, 85),
            'carbs': random.randint(250, 280),
            'fat': random.randint(60, 75),
            'fiber': random.randint(25, 30)
        },
        'goal_achievement': {
            'calories': random.randint(85, 95),
            'protein': random.randint(90, 100),
            'carbs': random.randint(80, 95),
            'fat': random.randint(85, 95)
        }
    }
    
    return Response(stats)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def guest_workout_logs(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    limit = int(request.GET.get('limit', 7))
    workout_types = ['Cardio', 'Strength Training', 'Yoga', 'HIIT', 'Swimming', 'Running']
    logs = []
    
    for i in range(limit):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        if random.random() > 0.3:
            logs.append({
                'id': f'workout-{i}',
                'date': date,
                'type': random.choice(workout_types),
                'duration': random.randint(30, 90),
                'calories_burned': random.randint(200, 500),
                'intensity': random.choice(['low', 'moderate', 'high']),
                'notes': f'Great {random.choice(workout_types).lower()} session!'
            })
    
    return Response({'count': len(logs), 'results': logs})

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def guest_recommendations_daily(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    recommendations = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'exercise': {
            'type': random.choice(['Cardio', 'Strength', 'Flexibility', 'Balance']),
            'duration': random.randint(30, 60),
            'intensity': random.choice(['moderate', 'high']),
            'description': 'Based on your recent activity, we recommend focusing on this type of exercise today.'
        },
        'nutrition': {
            'focus': random.choice(['Increase protein', 'More vegetables', 'Stay hydrated', 'Reduce sugar']),
            'target_calories': random.randint(1900, 2100),
            'water_intake': random.randint(8, 10),
            'tips': [
                'Eat a balanced breakfast',
                'Include lean protein in every meal',
                'Choose whole grains over refined',
                'Aim for 5 servings of fruits and vegetables'
            ]
        },
        'wellness': {
            'sleep_target': random.randint(7, 9),
            'stress_relief': random.choice(['Meditation', 'Deep breathing', 'Walk in nature', 'Yoga']),
            'daily_tip': 'Remember to take breaks and stretch every hour if you\'re sitting for long periods.'
        }
    }
    
    return Response(recommendations)

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def youtube_search(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = json.loads(request.body) if request.body else {}
        query = data.get('query', '')
        max_results = data.get('maxResults', 5)
        
        # YouTube API를 통한 검색은 get_workout_videos 함수를 활용
        result = get_workout_videos(query, 'all')
        
        if 'error' in result:
            return Response(result, status=status.HTTP_502_BAD_GATEWAY)
            
        # 결과를 프론트엔드가 기대하는 형식으로 변환
        items = result.get('items', [])
        formatted_items = []
        for item in items[:max_results]:
            formatted_items.append({
                'id': {'videoId': item['id']},
                'snippet': {
                    'title': item['title'],
                    'channelTitle': item.get('channel', 'Unknown'),
                    'thumbnails': {
                        'medium': {
                            'url': item.get('thumbnail', '')
                        }
                    }
                }
            })
        
        return Response({'items': formatted_items})
        
    except Exception as e:
        return Response({
            'error': f'YouTube search error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 새로운 API 엔드포인트들
@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def exercise_list(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    category = request.GET.get('category', '')
    difficulty = request.GET.get('difficulty', '')
    
    exercises = EXERCISE_DATA.copy()
    
    if category:
        exercises = [e for e in exercises if e['category'] == category]
    if difficulty:
        exercises = [e for e in exercises if e['difficulty'] == difficulty]
        
    return Response({'count': len(exercises), 'results': exercises})

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_routines(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return Response({'count': len(ROUTINE_DATA), 'results': ROUTINE_DATA})

@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
def youtube_music_recommendations(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    if request.method == 'GET':
        workout_type = request.GET.get('workout_type', 'general')
        result = get_youtube_music(workout_type)
    elif request.method == 'POST':
        data = json.loads(request.body) if request.body else {}
        exercise = data.get('exercise', 'general')
        mood = data.get('mood', 'energetic')
        # 운동과 기분을 조합하여 workout_type 생성
        workout_type = f"{exercise}_{mood}"
        result = get_youtube_music(workout_type)
    
    if 'error' in result:
        return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response(result)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_videos(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    exercise_type = request.GET.get('type', 'general')
    difficulty = request.GET.get('difficulty', 'beginner')
    result = get_workout_videos(exercise_type, difficulty)
    
    if 'error' in result:
        return Response(result, status=status.HTTP_502_BAD_GATEWAY)
    return Response(result)

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def analyze_nutrition(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = json.loads(request.body)
        food_description = data.get('food_description', '')
        
        analysis = analyze_food_simple(food_description)
        return Response(analysis)
        
    except Exception as e:
        return Response({
            'error': f'Nutrition analysis error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
def nutrition_tracking(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    if request.method == 'GET':
        date = request.GET.get('date', datetime.now().strftime('%Y-%m-%d'))
        nutrition_data = get_nutrition_mock_data(date)
        return Response(nutrition_data)
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        nutrition_info = {
            'food_name': data.get('food_name'),
            'quantity': data.get('quantity'),
            'meal_type': data.get('meal_type'),
            'calories': random.randint(100, 500),
            'protein': random.randint(5, 30),
            'carbs': random.randint(10, 60),
            'fat': random.randint(2, 25),
            'fiber': random.randint(1, 10),
            'added_at': datetime.now().isoformat()
        }
        
        return Response({'success': True, 'nutrition_info': nutrition_info})

@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
def social_feed(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    if request.method == 'GET':
        posts = get_social_posts()
        return Response({'count': len(posts), 'results': posts})
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        new_post = create_post(
            data.get('content'),
            data.get('workout_session_id'),
            data.get('image_url')
        )
        return Response({'success': True, 'post': new_post})

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def like_post(request, post_id):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    result = like_post_action(post_id)
    return Response(result)

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def health_consultation(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = json.loads(request.body)
        question = data.get('question', '')
        category = data.get('category', 'general')
        user_profile = data.get('user_profile', {})
        
        consultation = get_health_consultation(question, category, user_profile)
        return Response(consultation)
        
    except Exception as e:
        return Response({
            'error': f'Health consultation error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
