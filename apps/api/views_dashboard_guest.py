from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta

@api_view(['GET'])
@permission_classes([AllowAny])
def guest_daily_nutrition(request, date_str=None):
    """비회원용 일일 영양 정보 - 빈 데이터 반환"""
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    return Response({
        'date': date_str,
        'meals': [],
        'summary': {
            'total_calories': 0,
            'total_protein': 0,
            'total_carbs': 0,
            'total_fat': 0
        },
        'is_guest': True,
        'message': '비회원은 영양 정보가 저장되지 않습니다. 회원가입하시면 식단 관리 기능을 이용할 수 있습니다.'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_nutrition_statistics(request):
    """비회원용 영양 통계 - 빈 데이터 반환"""
    return Response({
        'statistics': {
            'average_calories': 0,
            'average_protein': 0,
            'average_carbs': 0,
            'average_fat': 0,
            'total_days': 0
        },
        'daily_data': [],
        'is_guest': True,
        'message': '비회원은 영양 통계를 확인할 수 없습니다.'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_workout_logs(request):
    """비회원용 운동 기록 - 빈 데이터 반환"""
    return Response({
        'results': [],
        'count': 0,
        'is_guest': True,
        'message': '비회원은 운동 기록이 저장되지 않습니다.'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_daily_recommendations(request):
    """비회원용 일일 추천"""
    return Response({
        'date': datetime.now().strftime('%Y-%m-%d'),
        'workout': {
            'title': '전신 스트레칭',
            'description': '하루를 시작하는 가벼운 스트레칭',
            'duration': 10,
            'difficulty': '초급',
            'exercises': [
                '목 스트레칭 (좌우 각 10초)',
                '어깨 돌리기 (앞뒤 각 10회)',
                '허리 트위스트 (좌우 각 10회)',
                '다리 스트레칭 (각 다리 15초)'
            ]
        },
        'nutrition': {
            'title': '균형잡힌 아침식사',
            'description': '에너지 넘치는 하루를 위한 아침 메뉴',
            'calories': 400,
            'menu': [
                '통곡물 토스트 2장',
                '스크램블 에그 2개',
                '아보카도 반 개',
                '오렌지 주스 1잔'
            ]
        },
        'tip': {
            'title': '수분 섭취의 중요성',
            'content': '하루 8잔 이상의 물을 마시면 신진대사가 활발해지고 피부 건강에도 도움이 됩니다.'
        },
        'is_guest': True,
        'message': '회원가입하시면 개인 맞춤 추천을 받을 수 있습니다!'
    }, status=status.HTTP_200_OK)
