from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime, timedelta
import random

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
