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
from .ai_service import get_chatbot
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
        # request.data를 사용하여 JSON 파싱
        username = request.data.get('username')
        password = request.data.get('password')
        
        # 디버깅을 위한 로그
        print(f"Login attempt - username: {username}")
        
        # 이메일로도 로그인 시도
        if '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                username = user_obj.username
            except User.DoesNotExist:
                pass
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'profile_image': None  # 프론트엔드가 기대하는 필드
                },
                'access': 'dummy-token',  # 프론트엔드가 토큰을 기대할 수 있음
                'refresh': 'dummy-refresh-token'
            })
        else:
            return Response({
                'success': False,
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        print(f"Login error: {str(e)}")
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
        # request.data 사용 (DRF 표준)
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        # 추가 프로필 정보
        birth_date = request.data.get('birth_date')
        gender = request.data.get('gender')
        height = request.data.get('height')
        weight = request.data.get('weight')
        diseases = request.data.get('diseases', [])
        health_conditions = request.data.get('health_conditions', [])
        allergies = request.data.get('allergies', [])
        fitness_level = request.data.get('fitness_level', 'beginner')
        
        print(f"Register attempt - username: {username}, email: {email}")
        
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
        
        # 자동 로그인
        login(request, user)
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'profile_image': None
            },
            'access': 'dummy-token',
            'refresh': 'dummy-refresh-token'
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
    
    # 인증된 사용자의 경우 실제 프로필 반환
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            from datetime import date
            today = date.today()
            age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)) if profile.birth_date else 30
            
            # BMI 계산
            bmi = None
            if profile.height and profile.weight:
                height_m = profile.height / 100
                bmi = profile.weight / (height_m ** 2)
            
            return Response({
                'age': age,
                'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
                'gender': profile.gender,
                'height': profile.height,
                'weight': profile.weight,
                'bmi': round(bmi, 1) if bmi else None,
                'body_fat_percentage': 18.5,  # 예시값
                'muscle_mass': 57.0,  # 예시값
                'fitness_level': profile.fitness_level,
                'health_score': 82,  # 예시값
                'diseases': profile.diseases,
                'allergies': profile.allergies,
                'last_updated': datetime.now().isoformat()
            })
        except UserProfile.DoesNotExist:
            pass
    
    # 게스트 사용자의 경우 기본값 반환
    return Response({
        'age': 30,
        'birth_date': '1994-01-01',  # 예시 생년월일
        'gender': 'male',
        'height': 175,
        'weight': 70,
        'bmi': 22.9,
        'body_fat_percentage': 18.5,
        'muscle_mass': 57.0,
        'fitness_level': 'intermediate',
        'health_score': 82,
        'diseases': [],
        'allergies': [],
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
        data = request.data  # DRF 표준
        question = data.get('question', '')
        category = data.get('category', 'general')
        
        # 사용자 정보 수집
        user_data = {
            'user_id': request.user.id if request.user.is_authenticated else 'guest',
            'username': request.user.username if request.user.is_authenticated else 'Guest',
        }
        
        # 프로필 정보 추가
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            profile = request.user.profile
            user_data.update({
                'birth_date': profile.birth_date,
                'gender': profile.gender,
                'height': profile.height,
                'weight': profile.weight,
                'diseases': profile.diseases,
                'allergies': profile.allergies,
                'fitness_level': profile.fitness_level
            })
        
        # AI 챗봇 사용
        chatbot = get_chatbot()
        result = chatbot.get_health_consultation(user_data, question)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'error': f'Health consultation error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 인증된 사용자를 위한 엔드포인트들
@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])  # TODO: 나중에 IsAuthenticated로 변경
def fitness_profile(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 인증된 사용자의 경우 실제 프로필 반환
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            from datetime import date
            today = date.today()
            age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)) if profile.birth_date else 30
            
            # BMI 계산
            bmi = None
            if profile.height and profile.weight:
                height_m = profile.height / 100
                bmi = profile.weight / (height_m ** 2)
            
            return Response({
                'age': age,
                'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
                'gender': profile.gender,
                'height': profile.height,
                'weight': profile.weight,
                'bmi': round(bmi, 1) if bmi else None,
                'body_fat_percentage': 18.5,  # 예시값
                'muscle_mass': 57.0,  # 예시값
                'fitness_level': profile.fitness_level,
                'health_score': 82,  # 예시값
                'diseases': profile.diseases,
                'allergies': profile.allergies,
                'last_updated': datetime.now().isoformat()
            })
        except UserProfile.DoesNotExist:
            pass
    
    # 게스트 사용자의 경우 기본값 반환
    return Response({
        'age': 30,
        'birth_date': '1994-01-01',  # 예시 생년월일
        'gender': 'male',
        'height': 175,
        'weight': 70,
        'bmi': 22.9,
        'body_fat_percentage': 18.5,
        'muscle_mass': 57.0,
        'fitness_level': 'intermediate',
        'health_score': 82,
        'diseases': [],
        'allergies': [],
        'last_updated': datetime.now().isoformat()
    })

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def daily_nutrition(request, date):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return guest_daily_nutrition(request, date)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def nutrition_statistics(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return guest_nutrition_statistics(request)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_logs(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return guest_workout_logs(request)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def recommendations_daily(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return guest_recommendations_daily(request)

# 소셜 기능 엔드포인트
@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def social_unread_count(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return Response({'unread_count': 0})

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def social_posts_feed(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    # social_feed와 동일한 데이터 반환
    posts = get_social_posts()
    return Response({'count': len(posts), 'results': posts})

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def social_stories(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 목 스토리 데이터
    stories = [
        {
            'id': 1,
            'user': {'id': 1, 'username': 'user1', 'profile_image': None},
            'content': '오늘의 운동 완료!',
            'image_url': None,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
        }
    ]
    return Response({'count': len(stories), 'results': stories})

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def user_level(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    return Response({
        'level': 5,
        'experience': 2500,
        'next_level_exp': 3000,
        'title': 'Fitness Enthusiast',
        'badges': [
            {'id': 1, 'name': '7-Day Streak', 'icon': 'fire'},
            {'id': 2, 'name': 'Early Bird', 'icon': 'sun'}
        ]
    })

# 채팅봇 엔드포인트
@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def chatbot_status(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 사용자 컨텍스트 수집
    user_context = {}
    has_profile = False
    
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            from datetime import date
            today = date.today()
            age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)) if profile.birth_date else 30
            
            user_context = {
                'age': age,
                'gender': profile.gender or 'unknown',
                'height': profile.height,
                'weight': profile.weight,
                'fitness_level': profile.fitness_level,
                'diseases': profile.diseases,
                'allergies': profile.allergies,
                'exercise_experience': profile.fitness_level
            }
            has_profile = True
        except UserProfile.DoesNotExist:
            pass
    
    return Response({
        'status': 'available',
        'user_context': user_context,
        'message_count': 0,
        'has_profile': has_profile
    })

@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
def chatbot_sessions(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    if request.method == 'POST':
        # 새 세션 생성
        session_id = f"session-{datetime.now().timestamp()}"
        return Response({
            'session_id': session_id,
            'created_at': datetime.now().isoformat()
        })
    
    # GET - 세션 목록
    return Response({
        'count': 0,
        'results': [],
        'active_session': None
    })

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def chatbot_sessions_active(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 게스트 세션 반환
    if not request.user.is_authenticated:
        return Response({
            'session': {
                'id': 'guest-session',
                'created_at': datetime.now().isoformat()
            },
            'session_id': 'guest-session'
        })
    
    return Response({
        'session': None,
        'session_id': None
    })

# 채팅봇 메인 API
@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def chatbot(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = request.data
        message = data.get('message', '')
        language = data.get('language', 'ko')
        
        # 사용자 정보 수집
        user_data = {
            'user_id': request.user.id if request.user.is_authenticated else 'guest',
            'username': request.user.username if request.user.is_authenticated else 'Guest',
        }
        
        # 프로필 정보 추가
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            profile = request.user.profile
            user_data.update({
                'birth_date': profile.birth_date,
                'gender': profile.gender,
                'height': profile.height,
                'weight': profile.weight,
                'diseases': profile.diseases,
                'allergies': profile.allergies,
                'fitness_level': profile.fitness_level
            })
        
        # AI 챗봇 사용
        chatbot = get_chatbot()
        result = chatbot.get_health_consultation(user_data, message)
        
        # 응답 형식 맞추기
        return Response({
            'success': result.get('success', True),
            'response': result.get('response', ''),
            'raw_response': result.get('response', ''),
            'sources': [],
            'user_context': user_data,
            'session_id': 'guest-session' if not request.user.is_authenticated else f"session-{request.user.id}"
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Chatbot error: {str(e)}',
            'response': '죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 누락된 소셜 알림 엔드포인트
@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def social_notifications_unread_count(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    return Response({
        'unread_count': random.randint(0, 5)  # 모의 데이터
    })

# AI 기반 운동 추천
@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def ai_workout_recommendation(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        # 사용자 정보 수집
        user_data = {
            'user_id': request.user.id if request.user.is_authenticated else 'guest',
            'username': request.user.username if request.user.is_authenticated else 'Guest',
        }
        
        # 요청 데이터
        data = request.data
        user_data.update({
            'goal': data.get('goal', '체중 감량'),
            'experience': data.get('experience', '초급'),
        })
        
        # 프로필 정보 추가
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            profile = request.user.profile
            user_data.update({
                'birth_date': profile.birth_date,
                'gender': profile.gender,
                'height': profile.height,
                'weight': profile.weight,
                'fitness_level': profile.fitness_level
            })
        
        # AI 챗봇 사용
        chatbot = get_chatbot()
        result = chatbot.generate_workout_recommendation(user_data)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'error': f'Workout recommendation error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# AI 기반 영양 추천
@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def ai_nutrition_recommendation(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        # 사용자 정보 수집
        user_data = {
            'user_id': request.user.id if request.user.is_authenticated else 'guest',
            'username': request.user.username if request.user.is_authenticated else 'Guest',
        }
        
        # 요청 데이터
        data = request.data
        user_data.update({
            'goal': data.get('goal', '균형 잡힌 식단'),
        })
        
        # 프로필 정보 추가
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            profile = request.user.profile
            user_data.update({
                'birth_date': profile.birth_date,
                'gender': profile.gender,
                'height': profile.height,
                'weight': profile.weight,
                'allergies': profile.allergies,
                'diseases': profile.diseases
            })
        
        # AI 챗봇 사용
        chatbot = get_chatbot()
        result = chatbot.generate_nutrition_recommendation(user_data)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'error': f'Nutrition recommendation error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
