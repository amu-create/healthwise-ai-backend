"""
Base views module - 기본 뷰 함수들
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime, timedelta
import random
import uuid


@api_view(['GET'])
def test_api(request):
    """API 작동 테스트"""
    return Response({
        'message': 'API is working!', 
        'method': request.method,
        'version': '1.0.0'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_profile(request):
    """게스트 프로필 정보"""
    return Response({
        'id': 'guest-123',
        'username': 'guest',
        'email': 'guest@example.com',
        'is_guest': True,
    })


@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def guest_login(request):
    """게스트 로그인"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 게스트 세션 생성
    guest_id = str(uuid.uuid4())
    
    return Response({
        'success': True,
        'guest_id': guest_id,
        'message': '게스트 모드로 접속했습니다.'
    })


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def guest_fitness_profile(request):
    """게스트 피트니스 프로필"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 인증된 사용자의 경우 실제 프로필 반환
    if request.user.is_authenticated:
        try:
            from api.models import UserProfile
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
def guest_workout_logs(request):
    """게스트 운동 로그"""
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
    """게스트 일일 추천"""
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


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def fitness_profile(request):
    """피트니스 프로필"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 인증된 사용자의 경우 실제 프로필 반환
    if request.user.is_authenticated:
        try:
            from api.models import UserProfile
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
def recommendations_daily(request):
    """일일 추천"""
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


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def user_level(request):
    """사용자 레벨 정보"""
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
