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

@api_view(['GET'])
def test_api(request):
    return Response({
        'message': 'API is working!',
        'method': request.method,
    })

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
    return Response({
        'csrfToken': get_token(request),
    })

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
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
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
    
    # Generate mock nutrition data
    meals = ['breakfast', 'lunch', 'dinner', 'snack']
    nutrition_data = {
        'date': date,
        'total_calories': random.randint(1800, 2200),
        'protein': random.randint(60, 90),
        'carbs': random.randint(200, 300),
        'fat': random.randint(50, 80),
        'fiber': random.randint(20, 35),
        'meals': []
    }
    
    for meal in meals:
        if random.random() > 0.2:  # 80% chance of having a meal
            nutrition_data['meals'].append({
                'type': meal,
                'calories': random.randint(300, 600),
                'protein': random.randint(15, 30),
                'carbs': random.randint(40, 80),
                'fat': random.randint(10, 25),
                'foods': [f'Sample {meal} food {i+1}' for i in range(random.randint(2, 4))]
            })
    
    return Response(nutrition_data)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def guest_nutrition_statistics(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # Get date range from query params
    start_date = request.GET.get('start_date', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Generate weekly statistics
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
    
    # Generate mock workout data
    workout_types = ['Cardio', 'Strength Training', 'Yoga', 'HIIT', 'Swimming', 'Running']
    logs = []
    
    for i in range(limit):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        if random.random() > 0.3:  # 70% chance of workout
            logs.append({
                'id': f'workout-{i}',
                'date': date,
                'type': random.choice(workout_types),
                'duration': random.randint(30, 90),
                'calories_burned': random.randint(200, 500),
                'intensity': random.choice(['low', 'moderate', 'high']),
                'notes': f'Great {random.choice(workout_types).lower()} session!'
            })
    
    return Response({
        'count': len(logs),
        'results': logs
    })

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
