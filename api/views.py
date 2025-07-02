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
import logging

logger = logging.getLogger(__name__)

# 서비스 모듈 import
from .services.data import HEALTH_OPTIONS, EXERCISE_DATA, ROUTINE_DATA
from .services.youtube_service import get_youtube_music, get_workout_videos
from .services.kakao_social_service import KakaoSocialService
from .services.nutrition_service import analyze_food_simple, get_nutrition_mock_data
from .services.social_service import get_social_posts, create_post, like_post_action
from .services.health_consultation import get_health_consultation
from .services.social_workout_service import social_workout_service
from .ai_service import get_chatbot
from .models import UserProfile
# Music API import
from .music.views import get_ai_keywords, youtube_search as music_youtube_search, save_feedback as music_save_feedback

# 기존 기본 API들
@api_view(['GET'])
def test_api(request):
    return Response({'message': 'API is working!', 'method': request.method})

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """DB 연결 상태를 확인하는 헬스체크 엔드포인트"""
    import django.db
    from django.db import connection
    
    result = {
        'status': 'ok',
        'api': 'running',
        'timestamp': datetime.now().isoformat(),
    }
    
    # DB 연결 테스트
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        result['database'] = 'connected'
        
        # 사용자 수 확인
        user_count = User.objects.count()
        result['users'] = user_count
        
        # 세션 테스트
        result['session_key'] = request.session.session_key or 'no-session'
        
    except Exception as e:
        result['database'] = 'error'
        result['db_error'] = str(e)
        result['status'] = 'error'
    
    # Redis 연결 테스트
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            result['redis'] = 'connected'
        else:
            result['redis'] = 'not working'
    except Exception as e:
        result['redis'] = 'error'
        result['redis_error'] = str(e)
    
    return Response(result)

@api_view(['GET'])
def guest_profile(request):
    return Response({
        'id': 'guest-123',
        'username': 'guest',
        'email': 'guest@example.com',
        'is_guest': True,
    })

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def guest_login(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 게스트 세션 생성
    import uuid
    guest_id = str(uuid.uuid4())
    
    return Response({
        'success': True,
        'guest_id': guest_id,
        'message': '게스트 모드로 접속했습니다.'
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
@permission_classes([AllowAny])  # 게스트도 로그아웃 가능하도록 변경
def auth_logout(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 게스트 사용자 확인
    is_guest = request.headers.get('X-Is-Guest') == 'true'
    
    if is_guest:
        # 게스트의 경우 그냥 성공 반환
        return Response({'success': True, 'message': 'Guest logout successful'})
    
    # 일반 사용자 로그아웃
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
        
        # 사용자 생성 (신호에서 UserProfile 자동 생성됨)
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # 프로필 업데이트 (이미 생성된 프로필을 가져와서 업데이트)
        profile = user.profile  # 신호에서 자동 생성된 프로필
        
        profile.fitness_level = fitness_level
        profile.diseases = diseases
        profile.health_conditions = health_conditions
        profile.allergies = allergies
        
        if birth_date:
            profile.birth_date = birth_date
        if gender:
            profile.gender = gender
        if height:
            profile.height = float(height)
        if weight:
            profile.weight = float(weight)
            
        profile.save()
        
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
    
    # 세션에서 실제 운동 로그 가져오기
    session_logs = request.session.get('workout_logs', [])
    
    # 날짜별로 정렬 (최신순)
    session_logs.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # 실제 로그 먼저 추가
    logs = []
    for log in session_logs[:limit]:
        logs.append({
            'id': log.get('id', f'workout-{len(logs)}'),
            'date': log.get('date', datetime.now().strftime('%Y-%m-%d')),
            'type': log.get('routine_name', 'Strength Training'),
            'duration': log.get('duration', 30),  # 실제 운동 시간
            'calories_burned': log.get('calories_burned', 240),
            'intensity': log.get('intensity', 'moderate'),
            'notes': log.get('notes', '운동을 완료했습니다! 💪')
        })
    
    # 나머지 날짜는 랜덤 데이터로 채우기 (선택적)
    for i in range(len(logs), limit):
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

# youtube_search는 이제 music.views의 youtube_search를 사용
youtube_search = music_youtube_search

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
    # 프론트엔드가 배열을 기대하므로 배열로 반환
    return Response(ROUTINE_DATA)

# youtube_music_recommendations는 이제 music.views의 get_ai_keywords를 사용
youtube_music_recommendations = get_ai_keywords

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
        
        # 사용자 정보 수집 (게스트도 가능)
        user_data = None
        if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
            profile = request.user.userprofile
            user_data = {
                'allergies': profile.allergies,
                'diseases': profile.diseases,
                'fitness_goal': getattr(profile, 'fitness_goal', '건강 유지')
            }
        
        # Gemini AI 사용
        from .services.gemini_nutrition_service import get_gemini_analyzer
        analyzer = get_gemini_analyzer()
        result = analyzer.analyze_food_with_ai(food_description, user_data)
        
        if result.get('success'):
            return Response(result['analysis'])
        else:
            # 폴백: 기존 간단한 분석 사용
            analysis = analyze_food_simple(food_description)
            return Response(analysis)
        
    except Exception as e:
        logger.error(f'Nutrition analysis error: {str(e)}')
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
    
    # 직접 구현
    nutrition_data = get_nutrition_mock_data(date)
    return Response(nutrition_data)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def nutrition_statistics(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 직접 구현
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

@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_logs(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    if request.method == 'GET':
        limit = int(request.GET.get('limit', 7))
        workout_types = ['Cardio', 'Strength Training', 'Yoga', 'HIIT', 'Swimming', 'Running']
        logs = []
        
        # 인증된 사용자는 DB에서 가져오기
        if request.user.is_authenticated:
            from .models import WorkoutLog
            db_logs = WorkoutLog.objects.filter(user=request.user).order_by('-date', '-created_at')[:limit]
            
            for log in db_logs:
                logs.append({
                    'id': log.id,
                    'date': log.date.isoformat(),
                    'type': log.workout_name,
                    'duration': log.duration,
                    'calories_burned': log.calories_burned,
                    'intensity': 'moderate',  # 기본값
                    'notes': log.notes or '운동을 완료했습니다! 💪'
                })
        else:
            # 게스트는 세션에서 가져오기
            session_logs = request.session.get('workout_logs', [])
            session_logs.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            for log in session_logs[:limit]:
                logs.append({
                    'id': log.get('id', f'workout-{len(logs)}'),
                    'date': log.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'type': log.get('routine_name', 'Strength Training'),
                    'duration': log.get('duration', 30),
                    'calories_burned': log.get('calories_burned', 240),
                    'intensity': log.get('intensity', 'moderate'),
                    'notes': log.get('notes', '운동을 완료했습니다! 💪')
                })
        
        # 나머지는 랜덤 데이터로 채우기
        for i in range(len(logs), limit):
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
    
    elif request.method == 'POST':
        # 새로운 POST 로직 - 운동 완료 기록 생성
        try:
            data = request.data
            
            # 필수 필드 검증
            if not data.get('routine_id'):
                return Response({
                    'error': 'routine_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 운동 로그 생성
            workout_log = {
                'id': random.randint(1000, 9999),
                'routine_id': data.get('routine_id'),
                'user_id': request.user.id if request.user.is_authenticated else 'guest',
                'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'duration': data.get('duration', 30),
                'calories_burned': data.get('duration', 30) * 8,  # 대략적인 칼로리 계산
                'notes': data.get('notes', ''),
                'created_at': datetime.now().isoformat(),
                'is_guest': not request.user.is_authenticated
            }
            
            # 세션에 저장 (임시 저장소)
            if not hasattr(request.session, '_workout_logs'):
                request.session._workout_logs = []
            request.session._workout_logs.append(workout_log)
            
            return Response(workout_log, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def recommendations_daily(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 직접 구현
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

# 소셜 기능 엔드포인트
@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def social_unread_count(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return Response({'unread_count': 0})

@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
def social_posts_feed(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    if request.method == 'GET':
        # feed_type 파라미터 처리
        feed_type = request.GET.get('feed_type', 'all')
        
        # 피드 타입에 따른 게시물 반환
        posts = get_social_posts()
        
        # 프론트엔드가 기대하는 형식으로 응답
        return Response({
            'count': len(posts), 
            'results': posts,
            'next': None,
            'previous': None
        })
    
    elif request.method == 'POST':
        # social_posts_create와 동일한 로직
        return social_posts_create(request)

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def social_posts_create(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        # 게스트 사용자 체크
        is_guest = not request.user.is_authenticated or request.headers.get('X-Is-Guest') == 'true'
        
        if is_guest:
            return Response({
                'success': False,
                'error': '게스트 사용자는 포스트를 작성할 수 없습니다.',
                'message': '회원가입 후 이용해주세요.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # multipart/form-data 처리
        content = request.data.get('content', '')
        visibility = request.data.get('visibility', 'public')
        media_file = request.FILES.get('media_file')
        workout_session_id = request.data.get('workout_session_id')
        workout_log_id = request.data.get('workout_log_id')
        
        # 컨텐츠가 비어있으면 에러
        if not content and not media_file:
            return Response({
                'success': False,
                'error': 'Content or image is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 파일 처리 (media_file이 있는 경우)
        image_url = None
        if media_file:
            # 파일 크기 체크 (10MB 제한)
            if media_file.size > 10 * 1024 * 1024:
                return Response({
                    'success': False,
                    'error': '파일 크기는 10MB를 초과할 수 없습니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 파일 타입 체크
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if media_file.content_type not in allowed_types:
                return Response({
                    'success': False,
                    'error': '지원하지 않는 파일 형식입니다. (JPEG, PNG, GIF, WebP만 가능)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 여기서는 간단히 URL만 생성 (실제로는 S3 등에 업로드 필요)
            image_url = f'/media/posts/{media_file.name}'
            # TODO: 실제 파일 업로드 처리
        
        # 새 게시물 생성
        new_post = {
            'id': random.randint(100, 999),
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'profile_image': None,  # TODO: 프로필 이미지 추가
                'profile_picture_url': None
            },
            'content': content,
            'image_url': image_url,
            'media_file': image_url,  # 프론트엔드가 media_file로 기대할 수 있음
            'visibility': visibility,
            'workout_session': workout_session_id,
            'workout_log_id': workout_log_id,
            'likes': [],
            'comments': [],
            'created_at': datetime.now().isoformat(),
            'is_liked': False,
            'is_saved': False,
            'likes_count': 0,
            'comments_count': 0,
            'shares_count': 0,
            'reactions': [],
            'tags': [],
            'mentions': []
        }
        
        # TODO: 실제 DB 저장 로직
        # if request.user.is_authenticated:
        #     post = Post.objects.create(
        #         user=request.user,
        #         content=content,
        #         visibility=visibility,
        #         ...
        #     )
        
        # 성공 응답
        return Response(new_post, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f'Social post create error: {str(e)}', exc_info=True)
        return Response({
            'error': f'Failed to create post: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    
    # GET - 세션 목록 (프론트엔드가 기대하는 형식)
    sessions = []
    
    # 사용자가 인증된 경우 기본 세션 추가
    if request.user.is_authenticated:
        sessions.append({
            'id': f"session-{request.user.id}",
            'created_at': datetime.now().isoformat(),
            'is_active': True,
            'message_count': 0
        })
    
    return Response({
        'count': len(sessions),
        'results': sessions,
        'next': None,
        'previous': None,
        'active_session': {
            'id': 'guest-session' if not request.user.is_authenticated else f"session-{request.user.id}",
            'created_at': datetime.now().isoformat()
        }
    })

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def chatbot_sessions_active(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 항상 활성 세션 반환
    session_id = 'guest-session' if not request.user.is_authenticated else f"session-{request.user.id}"
    
    return Response({
        'session': {
            'id': session_id,
            'created_at': datetime.now().isoformat(),
            'messages': []  # 빈 메시지 배열
        },
        'session_id': session_id
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
def social_notifications(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 모의 알림 데이터
    notifications = [
        {
            'id': 1,
            'type': 'like',
            'user': {'id': 2, 'username': 'user2', 'profile_image': None},
            'message': 'user2님이 당신의 게시물을 좋아합니다.',
            'created_at': datetime.now().isoformat(),
            'is_read': False
        },
        {
            'id': 2,
            'type': 'comment',
            'user': {'id': 3, 'username': 'user3', 'profile_image': None},
            'message': 'user3님이 당신의 게시물에 댓글을 달았습니다.',
            'created_at': (datetime.now() - timedelta(hours=2)).isoformat(),
            'is_read': True
        }
    ]
    
    page = int(request.GET.get('page', 1))
    page_size = 10
    start = (page - 1) * page_size
    end = start + page_size
    
    return Response({
        'count': len(notifications),
        'next': None,
        'previous': None,
        'results': notifications[start:end]
    })

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def social_notifications_unread_count(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    return Response({
        'unread_count': random.randint(0, 5)  # 모의 데이터
    })

# workout-logs POST를 위한 새 함수
@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_logs_create(request):
    """운동 로그 생성 (수정된 버전)"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = request.data
        
        # 필수 필드 검증
        if not data.get('routine_id'):
            return Response({
                'error': 'routine_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # duration 값 확인 및 정수로 변환
        duration = int(data.get('duration', 30))
        
        # 칼로리 계산 (운동 강도에 따라 다르게 계산)
        intensity_multiplier = {
            'low': 5,
            'moderate': 8,
            'high': 12
        }
        intensity = data.get('intensity', 'moderate')
        calories_per_minute = intensity_multiplier.get(intensity, 8)
        calories_burned = duration * calories_per_minute
        
        # 운동 로그 생성
        workout_log = {
            'id': random.randint(1000, 9999),
            'routine_id': data.get('routine_id'),
            'routine_name': data.get('routine_name', '운동 루틴'),
            'user_id': request.user.id if request.user.is_authenticated else 'guest',
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'duration': duration,  # 정수로 저장
            'calories_burned': calories_burned,
            'notes': data.get('notes', ''),
            'intensity': intensity,
            'created_at': datetime.now().isoformat(),
            'is_guest': not request.user.is_authenticated,
            'exercises_completed': data.get('exercises_completed', 0),
            'total_sets': data.get('total_sets', 0)
        }
        
        # 실제 DB 저장 로직
        if request.user.is_authenticated:
            from .models import WorkoutLog
            from datetime import datetime as dt
            
            db_log = WorkoutLog.objects.create(
                user=request.user,
                date=dt.strptime(data.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
                duration=duration,
                calories_burned=calories_burned,
                notes=data.get('notes', ''),
                workout_name=data.get('routine_name', '운동 루틴'),
                workout_type='gym',  # 기본값
            )
            workout_log['id'] = db_log.id
        else:
            # 게스트는 세션에 저장
            if 'workout_logs' not in request.session:
                request.session['workout_logs'] = []
            request.session['workout_logs'].append(workout_log)
            request.session.modified = True  # 세션 변경사항 저장 강제
        
        # 소셜 공유 처리
        share_to_social = data.get('share_to_social', False)
        social_post = None
        
        if share_to_social and request.user.is_authenticated:  # 게스트는 소셜 공유 불가
            user_id = request.user.id
            content = data.get('social_content', f'{duration}분 동안 운동을 완료했습니다! 💪')
            
            # 소셜 포스트 생성
            social_post = social_workout_service.create_workout_post(
                user_id=user_id,
                workout_log_id=workout_log['id'],
                content=content
            )
        
        # 응답 데이터
        response_data = {
            'workout_log': workout_log,
            'social_post': social_post
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f'Workout log create error: {str(e)}')
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

# 소셜 피드 - 인기 게시물
@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def social_posts_popular(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 인기 게시물 반환 (더 많은 좋아요를 받은 게시물)
    posts = get_social_posts()
    # 좋아요 수가 많은 순으로 정렬
    posts.sort(key=lambda x: x['likes_count'], reverse=True)
    
    return Response({
        'count': len(posts),
        'results': posts,
        'next': None,
        'previous': None
    })

# 소셜 피드 - 추천 게시물
@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def social_posts_recommended(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 추천 게시물 반환 (사용자 취향에 맞는 게시물)
    posts = get_social_posts()
    # 여기서는 무작위로 선택
    random.shuffle(posts)
    
    return Response({
        'count': len(posts),
        'results': posts,
        'next': None,
        'previous': None
    })

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

# 음악 피드백 저장은 이제 music.views의 save_feedback를 사용
music_save_feedback = music_save_feedback

# 프로필 API 엔드포인트
@api_view(['GET', 'PUT', 'OPTIONS'])
@permission_classes([AllowAny])  # 나중에 IsAuthenticated로 변경
def user_profile(request):
    """사용자 프로필 조회 및 수정"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 게스트 사용자 체크
    if not request.user.is_authenticated:
        return Response({
            'error': '로그인이 필요합니다.',
            'is_guest': True
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if request.method == 'GET':
        try:
            profile = UserProfile.objects.get(user=request.user)
            from datetime import date
            today = date.today()
            age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)) if profile.birth_date else None
            
            return Response({
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'profile': {
                    'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
                    'age': age,
                    'gender': profile.gender,
                    'height': profile.height,
                    'weight': profile.weight,
                    'diseases': profile.diseases,
                    'health_conditions': profile.health_conditions,
                    'allergies': profile.allergies,
                    'fitness_level': profile.fitness_level,
                    'fitness_goals': profile.fitness_goals,
                    'created_at': profile.created_at.isoformat(),
                    'updated_at': profile.updated_at.isoformat()
                }
            })
        except UserProfile.DoesNotExist:
            # 프로필이 없으면 기본값으로 생성
            profile = UserProfile.objects.create(user=request.user)
            return Response({
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'profile': {
                    'birth_date': None,
                    'age': None,
                    'gender': None,
                    'height': None,
                    'weight': None,
                    'diseases': [],
                    'health_conditions': [],
                    'allergies': [],
                    'fitness_level': 'beginner',
                    'fitness_goals': [],
                    'created_at': profile.created_at.isoformat(),
                    'updated_at': profile.updated_at.isoformat()
                }
            })
    
    elif request.method == 'PUT':
        try:
            profile = UserProfile.objects.get(user=request.user)
            data = request.data.get('profile', {})
            
            # 업데이트 가능한 필드들
            if 'birth_date' in data:
                profile.birth_date = data['birth_date']
            if 'gender' in data:
                profile.gender = data['gender']
            if 'height' in data:
                profile.height = float(data['height'])
            if 'weight' in data:
                profile.weight = float(data['weight'])
            if 'diseases' in data:
                profile.diseases = data['diseases']
            if 'health_conditions' in data:
                profile.health_conditions = data['health_conditions']
            if 'allergies' in data:
                profile.allergies = data['allergies']
            if 'fitness_level' in data:
                profile.fitness_level = data['fitness_level']
            if 'fitness_goals' in data:
                profile.fitness_goals = data['fitness_goals']
            
            profile.save()
            
            # 나이 계산
            from datetime import date
            today = date.today()
            age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)) if profile.birth_date else None
            
            return Response({
                'success': True,
                'message': '프로필이 업데이트되었습니다.',
                'profile': {
                    'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
                    'age': age,
                    'gender': profile.gender,
                    'height': profile.height,
                    'weight': profile.weight,
                    'diseases': profile.diseases,
                    'health_conditions': profile.health_conditions,
                    'allergies': profile.allergies,
                    'fitness_level': profile.fitness_level,
                    'fitness_goals': profile.fitness_goals,
                    'updated_at': profile.updated_at.isoformat()
                }
            })
        except UserProfile.DoesNotExist:
            return Response({
                'error': '프로필을 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'프로필 업데이트 오류: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 누락된 운동 관련 엔드포인트
@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_videos_list(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    search = request.GET.get('search', '')
    category = request.GET.get('category', 'all')
    
    # 유튜브 운동 비디오 검색
    if search:
        result = get_workout_videos(search, category)
    else:
        # 기본 운동 비디오 목록
        result = get_workout_videos('workout', category)
    
    if 'error' in result:
        return Response(result, status=status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)

# GIF가 있는 운동만 포함
VALID_EXERCISES_WITH_GIF = {
    "숄더프레스 머신": {"muscle_group": "어깨", "gif_url": "https://media1.tenor.com/m/vFJSvh8AvhAAAAAd/a1.gif"},
    "랙풀": {"muscle_group": "등", "gif_url": "https://media1.tenor.com/m/U-KW3hhwhxcAAAAd/gym.gif"},
    "런지": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/K8EFQDHYz3UAAAAd/gym.gif"},
    "덤벨런지": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/sZ7VwZ6jrbcAAAAd/gym.gif"},
    "핵스쿼트": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/jiqHF0MkHeYAAAAd/gym.gif"},
    "바벨스쿼트": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/pdMmsiutWkcAAAAd/gym.gif"},
    "레그익스텐션": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/bqKtsSuqilQAAAAd/gym.gif"},
    "레그컬": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/fj_cZPprAyMAAAAd/gym.gif"},
    "레그프레스": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/yBaS_oBgidsAAAAd/gym.gif"},
    "체스트프레스 머신": {"muscle_group": "가슴", "gif_url": "https://media1.tenor.com/m/3bJRUkfLN3EAAAAd/supino-na-maquina.gif"},
    "케이블 로프 트라이셉스푸시다운": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/mbebKudZjxYAAAAd/tr%C3%ADceps-pulley.gif"},
    "덤벨플라이": {"muscle_group": "가슴", "gif_url": "https://media1.tenor.com/m/oJXOnsC72qMAAAAd/crussifixo-no-banco-com-halteres.gif"},
    "인클라인 푸시업": {"muscle_group": "가슴", "gif_url": "https://media1.tenor.com/m/e45GckrMBLEAAAAd/flex%C3%A3o-inclinada-no-banco.gif"},
    "케이블 로프 오버헤드 익스텐션": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/Vq6LrVGUAKIAAAAd/tr%C3%ADceps-fraces-na-polia.gif"},
    "밀리터리 프레스": {"muscle_group": "어깨", "gif_url": "https://media1.tenor.com/m/CV1FfGVNpdcAAAAd/desenvolvimento-militar.gif"},
    "사이드레터럴레이즈": {"muscle_group": "어깨", "gif_url": "https://media1.tenor.com/m/-OavRqpxSaEAAAAd/eleva%C3%A7%C3%A3o-lateral.gif"},
    "삼두(맨몸)": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/iGyfarCUXe8AAAAd/tr%C3%ADceps-mergulho.gif"},
    "랫풀다운": {"muscle_group": "등", "gif_url": "https://media1.tenor.com/m/PVR9ra9tAwcAAAAd/pulley-pegada-aberta.gif"},
    "케이블 스트레이트바 트라이셉스 푸시다운": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/sxDebEfnoGcAAAAd/triceps-na-polia-alta.gif"},
    "머신 로우": {"muscle_group": "등", "gif_url": "https://media1.tenor.com/m/ft6FHrqty-8AAAAd/remada-pronada-maquina.gif"},
    "케이블 로우": {"muscle_group": "등", "gif_url": "https://media1.tenor.com/m/vy_b35185M0AAAAd/remada-baixa-triangulo.gif"},
    "라잉 트라이셉스": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/ToAHkKHVQP4AAAAd/on-lying-triceps-al%C4%B1n-press.gif"},
    "바벨 프리쳐 컬": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/m2Dfyh507FQAAAAd/8preacher-curl.gif"},
    "바벨로우": {"muscle_group": "등", "gif_url": "https://media1.tenor.com/m/AYJ_bNXDvoUAAAAd/workout-muscles.gif"},
    "풀업": {"muscle_group": "등", "gif_url": "https://media1.tenor.com/m/bOA5VPeUz5QAAAAd/noequipmentexercisesmen-pullups.gif"},
    "덤벨 체스트 프레스": {"muscle_group": "가슴", "gif_url": "https://media1.tenor.com/m/nxJqRDCmt0MAAAAd/supino-reto.gif"},
    "덤벨 컬": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/pXKe1wAZOlQAAAAd/b%C3%ADceps.gif"},
    "덤벨 트라이셉스 익스텐션": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/V3J-mg9gH0kAAAAd/seated-dumbbell-triceps-extension.gif"},
    "덤벨 고블릿 스쿼트": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/yvyaUSnqMXQAAAAd/agachamento-goblet-com-haltere.gif"},
    "컨센트레이션컬": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/jaX3EUxaQGkAAAAd/rosca-concentrada-no-banco.gif"},
    "해머컬": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/8T_oLOn1XJwAAAAd/rosca-alternada-com-halteres.gif"},
    "머신 이두컬": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/DJ-GuvjNCwgAAAAd/bicep-curl.gif"},
}

# 부위별 운동 목록
VALID_EXERCISES_BY_GROUP = {
    "가슴": ["체스트프레스 머신", "덤벨플라이", "인클라인 푸시업", "덤벨 체스트 프레스"],
    "등": ["랙풀", "랫풀다운", "머신 로우", "케이블 로우", "바벨로우", "풀업"],
    "하체": ["런지", "덤벨런지", "핵스쿼트", "바벨스쿼트", "레그익스텐션", "레그컬", "레그프레스", "덤벨 고블릿 스쿼트"],
    "어깨": ["숄더프레스 머신", "밀리터리 프레스", "사이드레터럴레이즈"],
    "팔": ["케이블 로프 트라이셉스푸시다운", "케이블 스트레이트바 트라이셉스 푸시다운", "케이블 로프 오버헤드 익스텐션", 
         "라잉 트라이셉스", "덤벨 트라이셉스 익스텐션", "삼두(맨몸)", "바벨 프리쳐 컬", "덤벨 컬", "해머컬", "컨센트레이션컬", "머신 이두컬"],
}

# 난이도별 추천 운동
EXERCISES_BY_LEVEL = {
    "초급": {
        "가슴": ["체스트프레스 머신", "인클라인 푸시업"],
        "등": ["랫풀다운", "머신 로우", "케이블 로우"],
        "하체": ["레그프레스", "레그익스텐션", "레그컬", "런지"],
        "어깨": ["숄더프레스 머신", "사이드레터럴레이즈"],
        "팔": ["덤벨 컬", "머신 이두컬", "케이블 로프 트라이셉스푸시다운"],
    },
    "중급": {
        "가슴": ["덤벨 체스트 프레스", "덤벨플라이"],
        "등": ["바벨로우", "랙풀", "풀업"],
        "하체": ["바벨스쿼트", "덤벨런지", "핵스쿼트", "덤벨 고블릿 스쿼트"],
        "어깨": ["밀리터리 프레스", "사이드레터럴레이즈"],
        "팔": ["바벨 프리쳐 컬", "해머컬", "라잉 트라이셉스", "삼두(맨몸)"],
    },
    "상급": {
        "가슴": ["덤벨 체스트 프레스", "덤벨플라이", "체스트프레스 머신"],
        "등": ["바벨로우", "풀업", "랙풀"],
        "하체": ["바벨스쿼트", "핵스쿼트", "런지", "덤벨런지"],
        "어깨": ["밀리터리 프레스", "숄더프레스 머신"],
        "팔": ["바벨 프리쳐 컬", "컨센트레이션컬", "케이블 로프 오버헤드 익스텐션"],
    }
}

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def ai_workout(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = request.data
        muscle_group = data.get('muscle_group', '전신')
        level = data.get('level', '초급')
        duration = data.get('duration', 30)
        equipment_available = data.get('equipment_available', True)
        specific_goals = data.get('specific_goals', '')
        
        # 게스트 사용자인지 확인
        is_guest = not request.user.is_authenticated
        
        # 게스트는 초급, 중급만 이용 가능
        if is_guest and level == "상급":
            level = "중급"
        
        # 유효한 운동 목록 가져오기
        if muscle_group == "전신":
            # 전신 운동인 경우 각 부위에서 골고루 선택
            if level == "초급":
                available_exercises = ["체스트프레스 머신", "랫풀다운", "레그프레스", "숄더프레스 머신", "덤벨 컬"]
            else:  # 중급
                available_exercises = ["덤벨 체스트 프레스", "바벨로우", "바벨스쿼트", "밀리터리 프레스", "해머컬"]
        elif muscle_group == "복근":
            # 복근은 GIF가 있는 운동이 없으므로 다른 부위 운동으로 대체
            available_exercises = ["런지", "레그익스텐션", "레그컬"]
        elif muscle_group in EXERCISES_BY_LEVEL.get(level, {}):
            available_exercises = EXERCISES_BY_LEVEL[level][muscle_group]
        elif muscle_group in VALID_EXERCISES_BY_GROUP:
            available_exercises = VALID_EXERCISES_BY_GROUP[muscle_group][:5] if is_guest else VALID_EXERCISES_BY_GROUP[muscle_group]
        else:
            # 기본값
            available_exercises = ["체스트프레스 머신", "랫풀다운", "레그프레스"]
        
        # 장비가 없는 경우 맨몸 운동만 선택
        if not equipment_available:
            bodyweight_exercises = ["인클라인 푸시업", "풀업", "런지", "삼두(맨몸)"]
            available_exercises = [ex for ex in available_exercises if ex in bodyweight_exercises]
            
            # 맨몸 운동이 부족한 경우 추가
            if len(available_exercises) < 3:
                available_exercises = ["인클라인 푸시업", "런지", "삼두(맨몸)"]
        
        # 운동 시간에 따른 운동 개수 결정
        if duration <= 30:
            num_exercises = 3
        else:
            num_exercises = min(4 if is_guest else 6, (duration // 15))
        
        # 운동 선택 (중복 제거)
        selected_exercises = []
        used_exercises = set()
        
        for exercise_name in available_exercises:
            if exercise_name not in used_exercises:
                selected_exercises.append(exercise_name)
                used_exercises.add(exercise_name)
                if len(selected_exercises) >= num_exercises:
                    break
        
        # 운동이 부족한 경우 다른 운동 추가
        if len(selected_exercises) < num_exercises:
            # 같은 근육군의 다른 운동들 추가
            if muscle_group in VALID_EXERCISES_BY_GROUP:
                for ex in VALID_EXERCISES_BY_GROUP[muscle_group]:
                    if ex not in used_exercises and len(selected_exercises) < num_exercises:
                        selected_exercises.append(ex)
                        used_exercises.add(ex)
            
            # 그래도 부족하면 전체 운동에서 추가
            if len(selected_exercises) < num_exercises:
                all_exercises = list(VALID_EXERCISES_WITH_GIF.keys())
                # random은 이미 import되어 있음 (파일 상단)
                random.shuffle(all_exercises)
                for ex in all_exercises:
                    if ex not in used_exercises and len(selected_exercises) < num_exercises:
                        selected_exercises.append(ex)
                        used_exercises.add(ex)
        
        # AI를 사용한 루틴 생성
        chatbot = get_chatbot()
        exercises_list = ", ".join(selected_exercises)
        
        prompt = f"""
        운동 루틴을 생성해주세요.
        - 운동 대상 부위: {muscle_group}
        - 운동 난이도: {level}
        - 운동 시간: {duration}분
        - 장비 사용 가능: {'예' if equipment_available else '아니오'}
        - 사용 가능한 운동: {exercises_list}
        
        각 운동마다 세트, 반복 횟수, 휴식 시간을 포함해서 알려주세요.
        난이도에 맞게 세트수와 반복수를 조절하세요:
        - 초급: 3세트, 10-12회
        - 중급: 3-4세트, 8-12회
        - 상급: 4-5세트, 6-10회
        
        JSON 형식으로 답변해주세요:
        {{
            "routine_name": "루틴 이름",
            "exercises": [
                {{
                    "name": "운동 이름",
                    "sets": 세트 수,
                    "reps": 반복 횟수,
                    "rest_seconds": 휴식 시간(초),
                    "notes": "수행 팁"
                }}
            ],
            "total_duration": 예상 시간
        }}
        """
        
        try:
            # AI 응답 받기
            response = chatbot.get_health_consultation(
                user_data={'user_id': request.user.id if request.user.is_authenticated else 'guest'},
                question=prompt
            )
            
            # JSON 파싱 시도
            import json
            content = response.get('response', '')
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            try:
                routine_data = json.loads(content)
            except:
                # JSON 파싱 실패 시 기본 루틴 생성
                raise ValueError("JSON parsing failed")
                
        except:
            # AI 실패 시 기본 루틴 생성
            routine_data = {
                "routine_name": f"{muscle_group} {level} 루틴",
                "exercises": [],
                "total_duration": duration
            }
            
            # 기본 세트/반복수 설정
            if level == "초급":
                sets, reps = 3, 12
            else:  # 중급
                sets, reps = 3, 10
            
            for exercise_name in selected_exercises[:num_exercises]:
                routine_data["exercises"].append({
                    "name": exercise_name,
                    "sets": sets,
                    "reps": reps,
                    "rest_seconds": 60 if level == "초급" else 75,
                    "notes": "정확한 자세로 천천히 수행하세요"
                })
        
        # 루틴 데이터 준비
        exercises_with_details = []
        added_exercises = set()
        
        for exercise_data in routine_data['exercises']:
            exercise_name = exercise_data['name']
            
            # 유효한 운동인지 확인 및 중복 체크
            if exercise_name not in VALID_EXERCISES_WITH_GIF or exercise_name in added_exercises:
                continue
            
            exercise_info = VALID_EXERCISES_WITH_GIF[exercise_name]
            added_exercises.add(exercise_name)
            
            exercises_with_details.append({
                'id': len(exercises_with_details) + 1,
                'exercise': {
                    'id': len(exercises_with_details) + 1,
                    'name': exercise_name,
                    'muscle_group': exercise_info['muscle_group'],
                    'gif_url': exercise_info['gif_url'],
                    'default_sets': exercise_data['sets'],
                    'default_reps': exercise_data['reps'],
                    'exercise_type': 'strength',
                    'description': f'{exercise_name} 운동'
                },
                'order': len(exercises_with_details) + 1,
                'sets': exercise_data['sets'],
                'reps': exercise_data['reps'],
                'recommended_weight': None,
                'notes': exercise_data.get('notes', '정확한 자세로 천천히 수행하세요')
            })
        
        # AI 생성 루틴 객체
        routine = {
            'id': random.randint(1000, 9999),  # 임시 ID
            'name': routine_data['routine_name'],
            'exercises': exercises_with_details,
            'level': level,
            'is_ai_generated': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_guest': is_guest
        }
        
        response_data = {
            'success': True,
            'routine': routine,
            'estimated_duration': routine_data.get('total_duration', duration)
        }
        
        if is_guest:
            response_data['guest_info'] = {
                'message': '더 많은 기능을 원하시면 회원가입을 해주세요.',
                'limited_features': ['초급, 중급 운동만 이용 가능', '최대 4개 운동까지 추천']
            }
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f'AI workout error: {str(e)}')
        return Response({
            'success': False,
            'error': f'AI workout error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
