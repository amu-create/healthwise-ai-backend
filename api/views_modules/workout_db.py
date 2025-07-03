from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime, timedelta
import random
import logging
from ..services.data import EXERCISE_DATA, ROUTINE_DATA
from ..services.youtube_service import get_workout_videos
from ..services.social_workout_service import social_workout_service
from ..ai_service import get_chatbot
from ..models import WorkoutLog, WorkoutSession
from django.utils import timezone

logger = logging.getLogger(__name__)

@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_logs_db(request):
    """DB 연동된 운동 로그 API"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    if request.method == 'GET':
        limit = int(request.GET.get('limit', 7))
        
        # 🔥 실제 DB에서 운동 로그 조회
        if request.user.is_authenticated:
            # 인증된 사용자: 실제 DB 데이터
            workout_logs = WorkoutLog.objects.filter(user=request.user).order_by('-date', '-created_at')[:limit]
            
            logs = []
            for log in workout_logs:
                logs.append({
                    'id': log.id,
                    'date': log.date.isoformat(),
                    'duration': log.duration,
                    'calories_burned': log.calories_burned or (log.duration * 8),
                    'workout_name': log.workout_name,
                    'exercise_name': log.workout_name,  # 대시보드 호환성
                    'routine_name': log.workout_name,   # 대시보드 호환성
                    'type': log.get_workout_type_display(),
                    'intensity': 'moderate',  # 기본값
                    'notes': log.notes,
                    'created_at': log.created_at.isoformat(),
                    'is_real_data': True
                })
            
            logger.info(f'[workout_logs_db] Returning {len(logs)} DB logs for user {request.user.id}')
            return Response({'count': len(logs), 'results': logs})
        
        else:
            # 게스트 사용자: 세션 기반 + 더미 데이터
            session_logs = getattr(request.session, '_workout_logs', [])
            
            if session_logs:
                recent_logs = session_logs[-limit:] if len(session_logs) > limit else session_logs
                logger.info(f'[workout_logs_db] Returning {len(recent_logs)} session logs for guest')
                return Response({'count': len(recent_logs), 'results': recent_logs})
            
            # 세션에도 데이터가 없으면 더미 데이터
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
                        'notes': f'Great {random.choice(workout_types).lower()} session!',
                        'is_real_data': False
                    })
            
            logger.info(f'[workout_logs_db] Returning {len(logs)} dummy logs for guest')
            return Response({'count': len(logs), 'results': logs})
    
    elif request.method == 'POST':
        # 🔥 실제 DB에 운동 완료 기록 저장
        try:
            data = request.data
            
            # 필수 필드 검증
            if not data.get('routine_id'):
                return Response({
                    'error': 'routine_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # duration을 정수로 변환
            duration = int(data.get('duration', 30))
            routine_name = data.get('routine_name', '운동 루틴')
            
            if request.user.is_authenticated:
                # 🔥 인증된 사용자: 실제 DB에 저장
                workout_log = WorkoutLog.objects.create(
                    user=request.user,
                    date=timezone.now().date(),
                    duration=duration,
                    calories_burned=duration * 8,  # 대략적인 칼로리 계산
                    workout_name=routine_name,
                    workout_type='gym',  # 기본값
                    notes=data.get('notes', ''),
                )
                
                # 응답 데이터
                response_data = {
                    'id': workout_log.id,
                    'routine_id': data.get('routine_id'),
                    'routine_name': routine_name,
                    'exercise_name': routine_name,  # 대시보드용 필드
                    'user_id': request.user.id,
                    'date': workout_log.date.isoformat(),
                    'duration': duration,
                    'calories_burned': workout_log.calories_burned,
                    'notes': workout_log.notes,
                    'created_at': workout_log.created_at.isoformat(),
                    'is_real_data': True,
                    'saved_to_db': True
                }
                
                logger.info(f'[workout_logs_db] Saved workout to DB for user {request.user.id}: {duration}min')
                return Response(response_data, status=status.HTTP_201_CREATED)
            
            else:
                # 게스트 사용자: 세션에 저장
                workout_log = {
                    'id': random.randint(1000, 9999),
                    'routine_id': data.get('routine_id'),
                    'routine_name': routine_name,
                    'exercise_name': routine_name,  # 대시보드용 필드
                    'user_id': 'guest',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'duration': duration,
                    'calories_burned': duration * 8,
                    'notes': data.get('notes', ''),
                    'created_at': datetime.now().isoformat(),
                    'is_guest': True,
                    'is_real_data': False
                }
                
                # 세션에 저장
                if not hasattr(request.session, '_workout_logs'):
                    request.session._workout_logs = []
                request.session._workout_logs.append(workout_log)
                request.session.modified = True
                
                logger.info(f'[workout_logs_db] Saved workout to session for guest: {duration}min')
                return Response(workout_log, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f'Workout log create error: {str(e)}')
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
