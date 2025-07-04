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
from ..models import WorkoutLog, WorkoutSession, WorkoutRoutine, Exercise, RoutineExercise
from django.utils import timezone

logger = logging.getLogger(__name__)

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
    
    # 기본 루틴 데이터
    routines = ROUTINE_DATA.copy()
    
    # 로그인 사용자의 경우 DB에서 저장된 루틴도 가져오기
    if request.user.is_authenticated:
        try:
            # 사용자의 루틴 가져오기
            user_routines = WorkoutRoutine.objects.filter(
                user=request.user
            ).prefetch_related('exercises', 'routineexercise_set').order_by('-created_at')
            
            # DB 루틴을 프론트엔드 형식으로 변환
            for routine in user_routines:
                routine_exercises = []
                
                # RoutineExercise를 통해 운동 정보 가져오기
                for re in routine.routineexercise_set.all().order_by('order'):
                    exercise = re.exercise
                    routine_exercises.append({
                        'id': exercise.id,
                        'name': exercise.name,
                        'sets': re.sets,
                        'reps': re.reps,
                        'duration': re.duration,
                        'rest_time': re.rest_time,
                        'category': exercise.category,
                        'difficulty': exercise.difficulty,
                        'description': exercise.description,
                        'gif_url': f'/static/images/exercises/{exercise.name.lower().replace(" ", "_")}.gif',
                        'order': re.order
                    })
                
                # 루틴 객체 생성
                routine_data = {
                    'id': routine.id,
                    'name': routine.name,
                    'description': routine.description,
                    'level': routine.difficulty,
                    'total_duration': routine.total_duration,
                    'exercises': routine_exercises,
                    'created_at': routine.created_at.isoformat(),
                    'updated_at': routine.updated_at.isoformat(),
                    'is_ai_generated': True,
                    'is_custom': True
                }
                
                # 사용자 루틴을 목록 앞에 추가
                routines.insert(0, routine_data)
                
            logger.info(f"Found {len(user_routines)} saved routines for user {request.user.id}")
            
        except Exception as e:
            logger.error(f"Error loading user routines: {str(e)}")
    
    # 프론트엔드가 배열을 기대하므로 배열로 반환
    return Response(routines)

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

@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_logs(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    if request.method == 'GET':
        # 기존 GET 로직
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
    
    elif request.method == 'POST':
        # 새로운 POST 로직 - 운동 완료 기록 생성
        try:
            data = request.data
            
            # 필수 필드 검증
            if not data.get('routine_id'):
                return Response({
                    'error': 'routine_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # duration 값 확인 및 안전한 정수 변환 (첫 번째)
            try:
                duration_value = data.get('duration', 30)
                logger.info(f"Received duration value: {duration_value} (type: {type(duration_value)})")
                
                if duration_value is None or duration_value == '':
                    duration = 30
                elif isinstance(duration_value, str):
                    # 문자열인 경우 숫자만 추출하여 변환
                    import re
                    numeric_str = re.sub(r'[^\d.]', '', str(duration_value))
                    duration = int(float(numeric_str)) if numeric_str else 30
                else:
                    # 숫자인 경우 NaN 체크 후 변환
                    if duration_value != duration_value:  # NaN 체크
                        duration = 30
                    else:
                        duration = int(float(duration_value))
                
                # 유효 범위 검증 (1분~300분)
                if duration < 1 or duration > 300:
                    logger.warning(f"Duration {duration} out of range, using default 30")
                    duration = 30
                    
            except (ValueError, TypeError, OverflowError) as e:
                logger.warning(f"Invalid duration value: {data.get('duration')}, using default 30. Error: {str(e)}")
                duration = 30
            
            # 운동 로그 생성
            workout_log = {
                'id': random.randint(1000, 9999),
                'routine_id': data.get('routine_id'),
                'user_id': request.user.id if request.user.is_authenticated else 'guest',
                'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'duration': duration,  # 정수로 저장
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
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    limit = int(request.GET.get('limit', 7))
    workout_types = ['Cardio', 'Strength Training', 'Yoga', 'HIIT', 'Swimming', 'Running']
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
                'type': random.choice(workout_types),
                'duration': random.randint(30, 90),
                'calories_burned': random.randint(200, 500),
                'intensity': random.choice(['low', 'moderate', 'high']),
                'notes': f'Great {random.choice(workout_types).lower()} session!'
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
        
        # duration 값 확인 및 안전한 정수 변환 (두 번째)
        try:
            duration_value = data.get('duration', 30)
            logger.info(f"Received duration value: {duration_value} (type: {type(duration_value)})")
            
            if duration_value is None or duration_value == '':
                duration = 30
            elif isinstance(duration_value, str):
                # 문자열인 경우 숫자만 추출하여 변환
                import re
                numeric_str = re.sub(r'[^\d.]', '', str(duration_value))
                duration = int(float(numeric_str)) if numeric_str else 30
            else:
                # 숫자인 경우 NaN 체크 후 변환
                if duration_value != duration_value:  # NaN 체크
                    duration = 30
                else:
                    duration = int(float(duration_value))
            
            # 유효 범위 검증 (1분~300분)
            if duration < 1 or duration > 300:
                logger.warning(f"Duration {duration} out of range, using default 30")
                duration = 30
                
        except (ValueError, TypeError, OverflowError) as e:
            logger.warning(f"Invalid duration value: {data.get('duration')}, using default 30. Error: {str(e)}")
            duration = 30
        
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
            'exercise_name': data.get('routine_name', '운동 루틴'),  # 대시보드용 필드 추가
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
        logger.info(f"AI workout request received: {request.data}")
        
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
            logger.info("Calling AI chatbot for workout generation...")
            response = chatbot.get_health_consultation(
                user_data={'user_id': request.user.id if request.user.is_authenticated else 'guest'},
                question=prompt
            )
            
            # 응답 성공 여부 확인
            if not response.get('success', False):
                logger.warning(f"AI response failed: {response.get('error', 'Unknown error')}")
                raise ValueError(f"AI response failed: {response.get('error', 'Unknown error')}")
            
            # JSON 파싱 시도
            import json
            content = response.get('response', '')
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            try:
                routine_data = json.loads(content)
            except Exception as parse_error:
                logger.warning(f"JSON parsing failed: {str(parse_error)}")
                # JSON 파싱 실패 시 기본 루틴 생성
                raise ValueError("JSON parsing failed")
                
        except Exception as e:
            logger.info(f"Using fallback routine due to: {str(e)}")
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
        
        # DB에 루틴 저장 (로그인 사용자만)
        saved_routine = None
        if request.user.is_authenticated:
            try:
                # WorkoutRoutine 생성
                saved_routine = WorkoutRoutine.objects.create(
                    user=request.user,
                    name=routine_data.get('routine_name', f'{muscle_group} {level} 루틴'),
                    description=f"AI가 생성한 {muscle_group} 운동 루틴 ({level})",
                    total_duration=routine_data.get('total_duration', duration),
                    difficulty=level,
                    is_public=False
                )
                
                # 각 운동을 RoutineExercise로 저장
                for idx, exercise_data in enumerate(routine_data.get('exercises', [])):
                    exercise_name = exercise_data.get('name', '')
                    
                    # 유효한 운동인지 확인
                    if exercise_name in VALID_EXERCISES_WITH_GIF:
                        # Exercise 찾기 또는 생성
                        exercise, created = Exercise.objects.get_or_create(
                            name=exercise_name,
                            defaults={
                                'category': muscle_group,
                                'description': f'{muscle_group} 운동',
                                'instructions': exercise_data.get('notes', '정확한 자세로 천천히 수행하세요'),
                                'duration': 5,  # 기본값
                                'calories_per_minute': 8.0,
                                'difficulty': 'easy' if level == '초급' else ('medium' if level == '중급' else 'hard'),
                                'muscle_groups': [muscle_group]
                            }
                        )
                        
                        # RoutineExercise 생성
                        RoutineExercise.objects.create(
                            routine=saved_routine,
                            exercise=exercise,
                            sets=exercise_data.get('sets', 3),
                            reps=exercise_data.get('reps', 12),
                            rest_time=exercise_data.get('rest_seconds', 60),
                            order=idx
                        )
                
                logger.info(f"AI 루틴 DB 저장 완료: {saved_routine.id}")
                
            except Exception as e:
                logger.error(f"AI 루틴 DB 저장 실패: {str(e)}")
                saved_routine = None
        
        # AI 생성 루틴 객체
        if saved_routine:
            # DB에 저장된 경우 실제 ID 사용
            routine = {
                'id': saved_routine.id,
                'name': saved_routine.name,
                'exercises': exercises_with_details,
                'level': level,
                'total_duration': saved_routine.total_duration,
                'is_ai_generated': True,
                'created_at': saved_routine.created_at.isoformat(),
                'updated_at': saved_routine.updated_at.isoformat(),
                'is_guest': False,
                'is_saved': True
            }
        else:
            # 게스트이거나 저장 실패시 임시 ID 사용
            routine = {
                'id': f'temp_{random.randint(1000, 9999)}',
                'name': routine_data['routine_name'],
                'exercises': exercises_with_details,
                'level': level,
                'total_duration': routine_data.get('total_duration', duration),
                'is_ai_generated': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_guest': is_guest,
                'is_saved': False
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
        logger.error(f'AI workout error: {str(e)}', exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'message': 'AI 운동 루틴 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
