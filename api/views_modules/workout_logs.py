# 운동 로그 관련 엔드포인트
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime, timedelta
import random
import logging

from ..services.social_workout_service import social_workout_service
from .workout_utils import safe_duration_convert
from .workout_constants import WORKOUT_TYPES, INTENSITY_MULTIPLIER

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_logs(request):
    """운동 로그 조회/생성"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    if request.method == 'GET':
        # 기존 GET 로직
        limit = int(request.GET.get('limit', 7))
        logs = []
        
        for i in range(limit):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            if random.random() > 0.3:
                logs.append({
                    'id': f'workout-{i}',
                    'date': date,
                    'type': random.choice(WORKOUT_TYPES),
                    'duration': random.randint(30, 90),
                    'calories_burned': random.randint(200, 500),
                    'intensity': random.choice(['low', 'moderate', 'high']),
                    'notes': f'Great {random.choice(WORKOUT_TYPES).lower()} session!'
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
            
            # duration 값 안전 변환
            duration = safe_duration_convert(data.get('duration', 30))
            
            # 운동 로그 생성
            workout_log = {
                'id': random.randint(1000, 9999),
                'routine_id': data.get('routine_id'),
                'user_id': request.user.id if request.user.is_authenticated else 'guest',
                'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'duration': duration,
                'calories_burned': duration * 8,  # 대략적인 칼로리 계산
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
            logger.error(f'Workout log creation error: {str(e)}')
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def guest_workout_logs(request):
    """게스트 운동 로그 조회"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    limit = int(request.GET.get('limit', 7))
    logs = []
    
    # 세션에서 실제 로그 가져오기
    if hasattr(request.session, '_workout_logs'):
        recent_logs = request.session._workout_logs[-limit:]
        return Response({'count': len(recent_logs), 'results': recent_logs})
    
    # 세션에 없으면 더미 데이터
    for i in range(limit):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        if random.random() > 0.3:
            logs.append({
                'id': f'workout-{i}',
                'date': date,
                'type': random.choice(WORKOUT_TYPES),
                'duration': random.randint(30, 90),
                'calories_burned': random.randint(200, 500),
                'intensity': random.choice(['low', 'moderate', 'high']),
                'notes': f'Great {random.choice(WORKOUT_TYPES).lower()} session!'
            })
    
    return Response({'count': len(logs), 'results': logs})


@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_logs_create(request):
    """운동 로그 생성 (수정된 버전)"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = request.data
        logger.info(f"Workout log create request data: {data}")
        
        # 필수 필드 검증
        if not data.get('routine_id'):
            return Response({
                'error': 'routine_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # duration 값 안전 변환
        duration = safe_duration_convert(data.get('duration', 30))
        
        # 칼로리 계산 (운동 강도에 따라 다르게 계산)
        intensity = data.get('intensity', 'moderate')
        calories_per_minute = INTENSITY_MULTIPLIER.get(intensity, 8)
        calories_burned = duration * calories_per_minute
        
        # 운동 로그 생성
        workout_log = {
            'id': random.randint(1000, 9999),
            'routine_id': data.get('routine_id'),
            'routine_name': data.get('routine_name', '운동 루틴'),
            'exercise_name': data.get('routine_name', '운동 루틴'),  # 대시보드용 필드 추가
            'user_id': request.user.id if request.user.is_authenticated else 'guest',
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'duration': duration,
            'calories_burned': calories_burned,
            'notes': data.get('notes', ''),
            'intensity': intensity,
            'created_at': datetime.now().isoformat(),
            'is_guest': not request.user.is_authenticated,
            'exercises_completed': data.get('exercises_completed', 0),
            'total_sets': data.get('total_sets', 0)
        }
        
        # 실제 DB 저장 로직 (Django 모델 사용 시)
        # if request.user.is_authenticated:
        #     WorkoutLog.objects.create(**workout_log)
        
        # 세션에 저장 (임시 저장소)
        if not hasattr(request.session, '_workout_logs'):
            request.session._workout_logs = []
        request.session._workout_logs.append(workout_log)
        
        # 소셜 공유 처리
        share_to_social = data.get('share_to_social', False)
        social_post = None
        
        if share_to_social and request.user.is_authenticated:  # 게스트는 소셜 공유 불가
            try:
                user_id = request.user.id
                content = data.get('social_content', f'{duration}분 동안 운동을 완료했습니다! 💪')
                
                # 소셜 포스트 생성
                social_post = social_workout_service.create_workout_post(
                    user_id=user_id,
                    workout_log_id=workout_log['id'],
                    content=content
                )
            except Exception as social_error:
                logger.warning(f'Social post creation failed: {str(social_error)}')
                # 소셜 포스트 실패해도 워크아웃 로그는 성공 처리
                social_post = None
        
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
