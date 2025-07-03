"""
DB 연동 운동 로그 시스템
실제 WorkoutLog 모델을 사용하여 회원별 운동 기록을 DB에 저장/조회
"""

import random
import logging
from datetime import datetime
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from api.models import WorkoutLog

logger = logging.getLogger(__name__)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_logs_db(request):
    """운동 로그 조회 (실제 DB 조회 버전)"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        # 게스트 사용자의 경우 세션에서 조회
        if not request.user.is_authenticated:
            session_logs = getattr(request.session, '_workout_logs', [])
            
            # 오늘 날짜 필터링
            today = datetime.now().strftime('%Y-%m-%d')
            today_logs = [log for log in session_logs if log.get('date') == today]
            
            # 전체 통계 계산
            total_duration = sum(log.get('duration', 0) for log in session_logs)
            total_calories = sum(log.get('calories_burned', 0) for log in session_logs)
            total_workouts = len(session_logs)
            
            return Response({
                'workout_logs': session_logs,
                'today_logs': today_logs,
                'summary': {
                    'total_duration': total_duration,
                    'total_calories': total_calories,
                    'total_workouts': total_workouts,
                    'today_duration': sum(log.get('duration', 0) for log in today_logs),
                    'today_calories': sum(log.get('calories_burned', 0) for log in today_logs),
                    'today_workouts': len(today_logs)
                }
            }, status=status.HTTP_200_OK)
        
        # 인증된 사용자의 경우 DB에서 조회
        user_logs = WorkoutLog.objects.filter(user=request.user).order_by('-date', '-created_at')
        
        # 로그 데이터 준비
        workout_logs = []
        for log in user_logs:
            workout_log = {
                'id': log.id,
                'routine_id': f'routine_{log.id}',  # 가상 routine_id
                'routine_name': log.workout_name,
                'exercise_name': log.workout_name,
                'user_id': log.user.id,
                'date': log.date.strftime('%Y-%m-%d'),
                'duration': log.duration,
                'calories_burned': log.calories_burned or 0,
                'notes': log.notes,
                'intensity': 'moderate',  # 기본값
                'created_at': log.created_at.isoformat(),
                'is_guest': False,
                'exercises_completed': 1,  # 기본값
                'total_sets': log.sets or 0,
                'workout_name': log.workout_name,
                'workout_type': log.workout_type
            }
            workout_logs.append(workout_log)
        
        # 오늘 로그 필터링
        today = timezone.now().date()
        today_logs = [log for log in workout_logs if log['date'] == today.strftime('%Y-%m-%d')]
        
        # 통계 계산
        total_duration = sum(log['duration'] for log in workout_logs)
        total_calories = sum(log['calories_burned'] for log in workout_logs)
        total_workouts = len(workout_logs)
        
        return Response({
            'workout_logs': workout_logs,
            'today_logs': today_logs,
            'summary': {
                'total_duration': total_duration,
                'total_calories': total_calories,
                'total_workouts': total_workouts,
                'today_duration': sum(log['duration'] for log in today_logs),
                'today_calories': sum(log['calories_burned'] for log in today_logs),
                'today_workouts': len(today_logs)
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Workout logs DB query error: {str(e)}')
        return Response({
            'error': str(e),
            'workout_logs': [],
            'today_logs': [],
            'summary': {
                'total_duration': 0,
                'total_calories': 0,
                'total_workouts': 0,
                'today_duration': 0,
                'today_calories': 0,
                'today_workouts': 0
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_logs_create_db(request):
    """운동 로그 생성 (실제 DB 저장 버전)"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = request.data
        logger.info(f"Creating workout log with data: {data}")
        
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
        
        # 게스트 사용자의 경우 세션 저장
        if not request.user.is_authenticated:
            workout_log = {
                'id': random.randint(1000, 9999),
                'routine_id': data.get('routine_id'),
                'routine_name': data.get('routine_name', '운동 루틴'),
                'exercise_name': data.get('routine_name', '운동 루틴'),
                'user_id': 'guest',
                'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'duration': duration,
                'calories_burned': calories_burned,
                'notes': data.get('notes', ''),
                'intensity': intensity,
                'created_at': datetime.now().isoformat(),
                'is_guest': True,
                'exercises_completed': data.get('exercises_completed', 0),
                'total_sets': data.get('total_sets', 0)
            }
            
            # 세션에 저장
            if not hasattr(request.session, '_workout_logs'):
                request.session._workout_logs = []
            request.session._workout_logs.append(workout_log)
            request.session.modified = True
            
            logger.info(f"Guest workout log saved to session: {workout_log}")
            
            return Response({
                'workout_log': workout_log,
                'social_post': None
            }, status=status.HTTP_201_CREATED)
        
        # 인증된 사용자의 경우 실제 DB 저장
        workout_log_data = {
            'user': request.user,
            'date': data.get('date', timezone.now().date()),
            'duration': duration,
            'calories_burned': calories_burned,
            'notes': data.get('notes', ''),
            'workout_name': data.get('routine_name', '운동 루틴'),
            'workout_type': data.get('workout_type', 'other')
        }
        
        # WorkoutLog 모델에 저장
        workout_log_obj = WorkoutLog.objects.create(**workout_log_data)
        
        logger.info(f"DB workout log created: {workout_log_obj.id}")
        
        # 응답용 데이터 준비 (대시보드 호환)
        workout_log = {
            'id': workout_log_obj.id,
            'routine_id': data.get('routine_id'),
            'routine_name': workout_log_obj.workout_name,
            'exercise_name': workout_log_obj.workout_name,
            'user_id': workout_log_obj.user.id,
            'date': workout_log_obj.date.strftime('%Y-%m-%d'),
            'duration': workout_log_obj.duration,
            'calories_burned': workout_log_obj.calories_burned,
            'notes': workout_log_obj.notes,
            'intensity': intensity,
            'created_at': workout_log_obj.created_at.isoformat(),
            'is_guest': False,
            'exercises_completed': data.get('exercises_completed', 0),
            'total_sets': data.get('total_sets', 0),
            'workout_name': workout_log_obj.workout_name,
            'workout_type': workout_log_obj.workout_type
        }
        
        # 응답 데이터
        response_data = {
            'workout_log': workout_log,
            'social_post': None
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f'Workout log create error: {str(e)}')
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
