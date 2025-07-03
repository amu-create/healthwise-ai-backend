from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.utils import timezone
import random
import json

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def nutrition_summary(request, date_str):
    """특정 날짜의 영양 요약 정보 반환"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        # 날짜 파싱
        date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # 목 데이터 생성
        summary = {
            'date': date_str,
            'total_calories': random.randint(1800, 2200),
            'consumed_calories': random.randint(1500, 2000),
            'calories_goal': 2000,
            'macros': {
                'protein': {
                    'current': random.randint(60, 80),
                    'goal': 75,
                    'unit': 'g'
                },
                'carbs': {
                    'current': random.randint(200, 250),
                    'goal': 250,
                    'unit': 'g'
                },
                'fat': {
                    'current': random.randint(50, 70),
                    'goal': 65,
                    'unit': 'g'
                },
                'fiber': {
                    'current': random.randint(20, 30),
                    'goal': 25,
                    'unit': 'g'
                }
            },
            'hydration': {
                'current': random.randint(1500, 2500),
                'goal': 2000,
                'unit': 'ml'
            },
            'meals': {
                'breakfast': random.randint(400, 600),
                'lunch': random.randint(500, 700),
                'dinner': random.randint(400, 600),
                'snacks': random.randint(100, 300)
            },
            'is_complete': False,
            'updated_at': datetime.now().isoformat()
        }
        
        return Response(summary)
        
    except ValueError:
        return Response({
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Error getting nutrition summary: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def guest_daily_nutrition(request):
    """게스트용 일일 영양 정보"""
    today = timezone.now().date()
    
    return Response({
        'date': today.isoformat(),
        'calories': {
            'consumed': random.randint(1500, 2000),
            'goal': 2000,
            'remaining': random.randint(0, 500)
        },
        'macros': {
            'protein': {'current': random.randint(60, 80), 'goal': 75, 'unit': 'g'},
            'carbs': {'current': random.randint(200, 250), 'goal': 250, 'unit': 'g'},
            'fat': {'current': random.randint(50, 70), 'goal': 65, 'unit': 'g'}
        },
        'meals': [
            {
                'id': 1,
                'type': 'breakfast',
                'name': '아침식사',
                'calories': random.randint(400, 600),
                'time': '08:00'
            },
            {
                'id': 2,
                'type': 'lunch',
                'name': '점심식사',
                'calories': random.randint(500, 700),
                'time': '12:30'
            }
        ]
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def guest_nutrition_statistics(request):
    """게스트용 영양 통계"""
    stats = []
    today = timezone.now().date()
    
    for i in range(7):
        date = today - timedelta(days=i)
        stats.append({
            'date': date.isoformat(),
            'calories': random.randint(1500, 2200),
            'protein': random.randint(60, 85),
            'carbs': random.randint(200, 280),
            'fat': random.randint(50, 75)
        })
    
    return Response({
        'weekly_stats': stats,
        'average': {
            'calories': sum(s['calories'] for s in stats) / len(stats),
            'protein': sum(s['protein'] for s in stats) / len(stats),
            'carbs': sum(s['carbs'] for s in stats) / len(stats),
            'fat': sum(s['fat'] for s in stats) / len(stats)
        }
    })

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def daily_nutrition(request):
    """일일 영양 정보"""
    if request.method == 'GET':
        today = timezone.now().date()
        return Response({
            'date': today.isoformat(),
            'user': request.user.username,
            'calories': {
                'consumed': random.randint(1500, 2000),
                'goal': 2000,
                'remaining': random.randint(0, 500)
            },
            'macros': {
                'protein': {'current': random.randint(60, 80), 'goal': 75, 'unit': 'g'},
                'carbs': {'current': random.randint(200, 250), 'goal': 250, 'unit': 'g'},
                'fat': {'current': random.randint(50, 70), 'goal': 65, 'unit': 'g'}
            }
        })
    
    # POST: 영양 정보 업데이트
    return Response({'message': 'Nutrition updated successfully'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nutrition_statistics(request):
    """영양 통계"""
    period = request.GET.get('period', 'week')
    stats = []
    today = timezone.now().date()
    
    days = 7 if period == 'week' else 30
    
    for i in range(days):
        date = today - timedelta(days=i)
        stats.append({
            'date': date.isoformat(),
            'calories': random.randint(1500, 2200),
            'protein': random.randint(60, 85),
            'carbs': random.randint(200, 280),
            'fat': random.randint(50, 75)
        })
    
    return Response({
        'period': period,
        'stats': stats,
        'average': {
            'calories': sum(s['calories'] for s in stats) / len(stats),
            'protein': sum(s['protein'] for s in stats) / len(stats),
            'carbs': sum(s['carbs'] for s in stats) / len(stats),
            'fat': sum(s['fat'] for s in stats) / len(stats)
        }
    })

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def nutrition_tracking(request):
    """영양 추적"""
    if request.method == 'GET':
        # 최근 식사 기록
        return Response({
            'recent_meals': [
                {
                    'id': 1,
                    'name': '닭가슴살 샐러드',
                    'calories': 350,
                    'protein': 45,
                    'carbs': 15,
                    'fat': 10,
                    'logged_at': timezone.now().isoformat()
                }
            ],
            'daily_total': {
                'calories': 1650,
                'protein': 78,
                'carbs': 210,
                'fat': 55
            }
        })
    
    # POST: 새 식사 기록
    return Response({
        'message': 'Meal logged successfully',
        'meal_id': random.randint(100, 999)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_nutrition(request):
    """영양 분석"""
    data = request.data
    
    # 간단한 분석 결과 반환
    return Response({
        'analysis': {
            'total_calories': data.get('calories', 0),
            'nutritional_value': 'Good' if data.get('calories', 0) < 500 else 'High',
            'recommendations': [
                'Consider adding more vegetables',
                'Good protein content'
            ]
        }
    })

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ai_nutrition_recommendation(request):
    """AI 영양 추천"""
    if request.method == 'GET':
        return Response({
            'recommendations': [
                {
                    'meal': '아침',
                    'suggestion': '오트밀과 과일',
                    'calories': 350,
                    'reason': '섬유질과 비타민이 풍부합니다'
                },
                {
                    'meal': '점심', 
                    'suggestion': '현미밥과 구운 닭가슴살',
                    'calories': 550,
                    'reason': '균형 잡힌 탄수화물과 단백질'
                }
            ],
            'daily_tips': [
                '물을 충분히 마시세요',
                '식사 간격을 일정하게 유지하세요'
            ]
        })
    
    # POST: 사용자 선호도 기반 추천
    preferences = request.data.get('preferences', {})
    return Response({
        'personalized_recommendations': [
            {
                'meal': '저녁',
                'suggestion': '연어 스테이크와 야채',
                'calories': 450,
                'matches_preferences': True
            }
        ]
    })
