from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.db import transaction
from django.core.cache import cache
import json
import logging
from datetime import datetime
from .models import Exercise, Routine, RoutineExercise
from .serializers import RoutineSerializer, AIWorkoutRequestSerializer
from .views_workout import VALID_EXERCISES_WITH_GIF, VALID_EXERCISES_BY_GROUP, EXERCISES_BY_LEVEL

from .guest_utils import check_guest_api_limit, get_or_create_guest_id, GUEST_API_LIMITS

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def ai_workout_recommendation_guest(request):
    """비회원을 위한 AI 운동 루틴 추천 (제한적)"""
    
    # API 호출 제한 확인
    allowed, count, limit, guest_id = check_guest_api_limit(request, 'AI_WORKOUT')
    if not allowed:
        return Response({
            'error': '일일 API 호출 제한을 초과했습니다.',
            'message': f'비회원은 하루에 {limit}회까지만 이용 가능합니다. 더 많은 기능을 이용하려면 회원가입을 해주세요.',
            'daily_limit': limit,
            'current_count': count,
            'guest_id': guest_id
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    serializer = AIWorkoutRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # 운동 부위와 난이도에 따른 운동 선택
    muscle_group = data['muscle_group']
    level = data['level']
    equipment_available = data.get('equipment_available', True)
    duration = data['duration']
    
    # 비회원은 초급, 중급만 이용 가능
    if level == "상급":
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
        available_exercises = VALID_EXERCISES_BY_GROUP[muscle_group][:5]  # 비회원은 최대 5개까지
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
    
    # 운동 시간에 따른 운동 개수 결정 (비회원은 최대 4개)
    if duration <= 30:
        num_exercises = 3
    else:
        num_exercises = min(4, (duration // 15))
    
    # 운동 선택 (중복 제거 강화)
    selected_exercises = []
    used_exercises = set()  # 중복 방지를 위한 set
    
    # 우선 available_exercises에서 선택
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
            # 랜덤하게 섞어서 다양성 확보
            import random
            random.shuffle(all_exercises)
            for ex in all_exercises:
                if ex not in used_exercises and len(selected_exercises) < num_exercises:
                    selected_exercises.append(ex)
                    used_exercises.add(ex)
    
    # GPT 프롬프트 생성
    exercises_list = ", ".join(selected_exercises)
    prompt = f"""
    당신은 전문 피트니스 트레이너입니다. 사용자에게 맞춤 운동 루틴을 설계해야 합니다.

    [사용자 정보]
    - 운동 대상 부위: {data['muscle_group']}
    - 운동 난이도: {level}
    - 운동 시간: {data['duration']}분
    - 장비 사용 가능: {'예' if equipment_available else '아니오'}
    - 사용자 유형: 비회원 (기본 루틴)

    [사용 가능한 운동]
    다음 운동들만 사용하여 루틴을 구성하세요: {exercises_list}

    [루틴 설계 기준]
    1. 위에 제공된 운동만 사용하세요. 절대 다른 운동을 추가하지 마세요.
    2. 총 {num_exercises}개의 운동으로 구성하세요.
    3. 각 운동마다 다음 정보를 JSON 형식으로 작성하세요:
    {{
        "exercises": [
            {{
                "name": "운동 이름 (제공된 목록에서만)",
                "muscle_group": "{muscle_group}",
                "sets": 세트 수 (숫자),
                "reps": 반복 횟수 (숫자),
                "rest_seconds": 휴식 시간(초),
                "notes": "수행 팁"
            }}
        ],
        "routine_name": "{muscle_group} {level} 루틴",
        "total_duration": {duration}
    }}
    4. 난이도에 맞게 세트수와 반복수를 조절하세요:
       - 초급: 3세트, 10-12회
       - 중급: 3-4세트, 8-12회
    5. 응답은 JSON 형식으로만 작성하세요.
    """
    
    try:
        # OpenAI 클라이언트 사용
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional fitness trainer. Only use the exercises provided in the prompt. Never add exercises not in the list."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500  # 비회원은 토큰 제한
        )
        
        # 응답 파싱
        content = response.choices[0].message.content
        try:
            routine_data = json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse GPT response: {content}")
            # 수동으로 루틴 생성
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
            
            for i, exercise_name in enumerate(selected_exercises[:num_exercises]):
                routine_data["exercises"].append({
                    "name": exercise_name,
                    "muscle_group": muscle_group,
                    "sets": sets,
                    "reps": reps,
                    "rest_seconds": 60 if level == "초급" else 75,
                    "notes": "정확한 자세로 천천히 수행하세요"
                })
        
        # 루틴 데이터 준비 (DB에 저장하지 않음)
        exercises_with_details = []
        added_exercises = set()  # 중복 방지
        
        for exercise_data in routine_data['exercises']:
            exercise_name = exercise_data['name']
            
            # 유효한 운동인지 확인 및 중복 체크
            if exercise_name not in VALID_EXERCISES_WITH_GIF or exercise_name in added_exercises:
                continue
            
            exercise_info = VALID_EXERCISES_WITH_GIF[exercise_name]
            added_exercises.add(exercise_name)
            
            exercises_with_details.append({
                'name': exercise_name,
                'muscle_group': exercise_info['muscle_group'],
                'gif_url': exercise_info['gif_url'],
                'sets': exercise_data['sets'],
                'reps': exercise_data['reps'],
                'rest_seconds': exercise_data.get('rest_seconds', 60),
                'notes': exercise_data.get('notes', '')
            })
        
        return Response({
            'routine': {
                'name': routine_data['routine_name'],
                'level': level,
                'exercises': exercises_with_details,
                'is_guest': True
            },
            'estimated_duration': routine_data.get('total_duration', duration),
            'guest_info': {
                'daily_limit': limit,
                'remaining': limit - count,
                'message': f'오늘 {count}/{limit}회 이용했습니다. 더 많은 기능을 원하시면 회원가입을 해주세요.',
                'guest_id': guest_id
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"AI workout recommendation error: {str(e)}")
        
        # 에러 발생 시 기본 루틴 반환
        if level == "초급":
            sets, reps = 3, 12
        else:  # 중급
            sets, reps = 3, 10
        
        exercises_with_details = []
        added_exercises_fallback = set()  # 중복 방지
        
        for exercise_name in selected_exercises[:num_exercises]:
            if exercise_name in VALID_EXERCISES_WITH_GIF and exercise_name not in added_exercises_fallback:
                exercise_info = VALID_EXERCISES_WITH_GIF[exercise_name]
                added_exercises_fallback.add(exercise_name)
                
                exercises_with_details.append({
                    'name': exercise_name,
                    'muscle_group': exercise_info['muscle_group'],
                    'gif_url': exercise_info['gif_url'],
                    'sets': sets,
                    'reps': reps,
                    'rest_seconds': 60 if level == "초급" else 75,
                    'notes': "정확한 자세로 천천히 수행하세요"
                })
        
        return Response({
            'routine': {
                'name': f"{muscle_group} {level} 기본 루틴",
                'level': level,
                'exercises': exercises_with_details,
                'is_guest': True
            },
            'estimated_duration': duration,
            'guest_info': {
                'daily_limit': limit,
                'remaining': limit - count,
                'message': f'오늘 {count}/{limit}회 이용했습니다. 더 많은 기능을 원하시면 회원가입을 해주세요.',
                'guest_id': guest_id
            }
        }, status=status.HTTP_200_OK)
