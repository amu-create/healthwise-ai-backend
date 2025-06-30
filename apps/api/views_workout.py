# 운동별 고정된 팁
EXERCISE_TIPS = {
    "체스트프레스 머신": "가슴 근육에 집중하세요",
    "덤벨플라이": "가슴 근육에 집중하세요",
    "인클라인 푸시업": "허리를 곧게 펴고 코어에 힘을 주세요",
    "덤벨 체스트 프레스": "가슴 근육에 집중하세요",
    "랙풀": "등 근육에 집중하세요",
    "랫풀다운": "등 근육에 집중하세요",
    "머신 로우": "등 근육에 집중하세요",
    "케이블 로우": "등 근육에 집중하세요",
    "바벨로우": "등 근육에 집중하세요",
    "풀업": "허리를 곧게 펴고 코어에 힘을 주세요",
    "런지": "무릎이 발끝을 넘지 않도록 주의하세요",
    "덤벨런지": "무릎이 발끝을 넘지 않도록 주의하세요",
    "핵스쿼트": "무릎이 발끝을 넘지 않도록 주의하세요",
    "바벨스쿼트": "무릎이 발끝을 넘지 않도록 주의하세요",
    "레그익스텐션": "무게를 천천히 컨트롤하세요",
    "레그컴": "무게를 천천히 컨트롤하세요",
    "레그프레스": "무릎이 발끝을 넘지 않도록 주의하세요",
    "덤벨 고블릿 스쿼트": "무릎이 발끝을 넘지 않도록 주의하세요",
    "숙더프레스 머신": "어깨에 무리가 가지 않도록 주의하세요",
    "밀리터리 프레스": "어깨에 무리가 가지 않도록 주의하세요",
    "사이드레터럴레이즈": "어깨에 무리가 가지 않도록 주의하세요",
    "케이블 로프 트라이셉스푸시다운": "팔꿈치를 고정하고 팔만 움직이세요",
    "케이블 스트레이트바 트라이셉스 푸시다운": "팔꿈치를 고정하고 팔만 움직이세요",
    "케이블 로프 오버헤드 익스텐션": "팔꿈치를 고정하고 팔만 움직이세요",
    "라잉 트라이셉스": "팔꿈치를 고정하고 팔만 움직이세요",
    "덤벨 트라이셉스 익스텐션": "팔꿈치를 고정하고 팔만 움직이세요",
    "삼두(맨몸)": "복근에 힘을 주고 수행하세요",
    "바벨 프리처 컴": "팔꿈치를 고정하고 팔만 움직이세요",
    "덤벨 컴": "팔꿈치를 고정하고 팔만 움직이세요",
    "해머컴": "팔꿈치를 고정하고 팔만 움직이세요",
    "컨센트레이션컴": "팔꿈치를 고정하고 팔만 움직이세요",
    "머신 이두컴": "팔꿈치를 고정하고 팔만 움직이세요",
}

# 기본 팁 (특정 운동에 대한 팁이 없을 경우)
DEFAULT_TIP = "정확한 자세로 천천히 수행하세요"

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.db import transaction
import json
import logging
from datetime import date
from .models import (
    Exercise, Routine, RoutineExercise, FitnessProfile,
    WorkoutRoutineLog, FoodAnalysis, DailyNutrition
)
from .serializers.workout import (
    ExerciseSerializer, RoutineSerializer, FitnessProfileSerializer,
    WorkoutRoutineLogSerializer, AIWorkoutRequestSerializer,
    FoodAnalysisSerializer, FoodAnalysisRequestSerializer,
    DailyNutritionSerializer
)

logger = logging.getLogger(__name__)

# GIF가 있는 운동만 포함 (정확히 32개)
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

# 부위별 운동 목록 (GIF가 있는 운동만)
VALID_EXERCISES_BY_GROUP = {
    "가슴": ["체스트프레스 머신", "덤벨플라이", "인클라인 푸시업", "덤벨 체스트 프레스"],
    "등": ["랙풀", "랫풀다운", "머신 로우", "케이블 로우", "바벨로우", "풀업"],
    "하체": ["런지", "덤벨런지", "핵스쿼트", "바벨스쿼트", "레그익스텐션", "레그컬", "레그프레스", "덤벨 고블릿 스쿼트"],
    "어깨": ["숄더프레스 머신", "밀리터리 프레스", "사이드레터럴레이즈"],
    "팔": ["케이블 로프 트라이셉스푸시다운", "케이블 스트레이트바 트라이셉스 푸시다운", "케이블 로프 오버헤드 익스텐션", 
         "라잉 트라이셉스", "덤벨 트라이셉스 익스텐션", "삼두(맨몸)", "바벨 프리쳐 컬", "덤벨 컬", "해머컬", "컨센트레이션컬", "머신 이두컬"],
}

# 난이도별 추천 운동 (GIF가 있는 운동만)
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exercise_list(request):
    """운동 목록 조회"""
    muscle_group = request.query_params.get('muscle_group')
    exercise_type = request.query_params.get('exercise_type')
    
    exercises = Exercise.objects.all()
    
    if muscle_group:
        exercises = exercises.filter(muscle_group__icontains=muscle_group)
    if exercise_type:
        exercises = exercises.filter(exercise_type=exercise_type)
    
    serializer = ExerciseSerializer(exercises, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def routine_list(request):
    """루틴 목록 조회 및 생성"""
    if request.method == 'GET':
        routines = Routine.objects.filter(user=request.user)
        serializer = RoutineSerializer(routines, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = RoutineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def routine_detail(request, pk):
    """루틴 상세 조회, 수정, 삭제"""
    try:
        routine = Routine.objects.get(pk=pk, user=request.user)
    except Routine.DoesNotExist:
        return Response(
            {"error": "루틴을 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = RoutineSerializer(routine)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = RoutineSerializer(routine, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        routine.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_workout_recommendation(request):
    """AI 운동 루틴 추천"""
    serializer = AIWorkoutRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # 사용자 피트니스 프로필 가져오기
    try:
        fitness_profile = FitnessProfile.objects.get(user=request.user)
    except FitnessProfile.DoesNotExist:
        fitness_profile = None
    
    # 운동 부위와 난이도에 따른 운동 선택
    muscle_group = data['muscle_group']
    level = data['level']
    equipment_available = data['equipment_available']
    
    # 유효한 운동 목록 가져오기
    if muscle_group == "전신":
        # 전신 운동인 경우 각 부위에서 골고루 선택
        available_exercises = []
        if level == "초급":
            available_exercises = ["체스트프레스 머신", "랫풀다운", "레그프레스", "숄더프레스 머신", "덤벨 컬"]
        elif level == "중급":
            available_exercises = ["덤벨 체스트 프레스", "바벨로우", "바벨스쿼트", "밀리터리 프레스", "해머컬"]
        else:
            available_exercises = ["덤벨플라이", "풀업", "핵스쿼트", "밀리터리 프레스", "바벨 프리쳐 컬"]
    elif muscle_group == "복근":
        # 복근은 GIF가 있는 운동이 없으므로 다른 부위 운동으로 대체
        available_exercises = ["런지", "레그익스텐션", "레그컬"]
    elif muscle_group in EXERCISES_BY_LEVEL.get(level, {}):
        available_exercises = EXERCISES_BY_LEVEL[level][muscle_group]
    elif muscle_group in VALID_EXERCISES_BY_GROUP:
        available_exercises = VALID_EXERCISES_BY_GROUP[muscle_group]
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
    duration = data['duration']
    if duration <= 30:
        num_exercises = 3
    elif duration <= 45:
        num_exercises = 4
    elif duration <= 60:
        num_exercises = 5
    else:
        num_exercises = 6
    
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
    
    # 운동이 부족한 경우 다른 운동 추가 (GIF가 있는 운동만)
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
    - 운동 난이도: {data['level']}
    - 운동 시간: {data['duration']}분
    - 장비 사용 가능: {'예' if data['equipment_available'] else '아니오'}
    """
    
    if fitness_profile:
        prompt += f"""
    - 경험: {fitness_profile.get_experience_display()}
    - 목표: {fitness_profile.get_goal_display()}
    - 체중: {fitness_profile.weight}kg
    - 신장: {fitness_profile.height}cm
    """
    
    if data.get('specific_goals'):
        prompt += f"\n    - 특별 목표: {data['specific_goals']}"
    
    prompt += f"""

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
       - 상급: 4-5세트, 6-10회
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
            temperature=0.7
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
            elif level == "중급":
                sets, reps = 4, 10
            else:
                sets, reps = 4, 8
            
            for i, exercise_name in enumerate(selected_exercises[:num_exercises]):
                routine_data["exercises"].append({
                    "name": exercise_name,
                    "muscle_group": muscle_group,
                    "sets": sets,
                    "reps": reps,
                    "rest_seconds": 60 if level == "초급" else 90,
                    "notes": "정확한 자세로 천천히 수행하세요"
                })
        
        # 루틴 생성
        with transaction.atomic():
            routine = Routine.objects.create(
                name=routine_data['routine_name'],
                level=data['level'],
                user=request.user,
                is_ai_generated=True
            )
            
            # 운동 추가
            added_to_routine = set()  # 루틴에 추가된 운동 추적
            
            for idx, exercise_data in enumerate(routine_data['exercises']):
                exercise_name = exercise_data['name']
                
                # 유효한 운동인지 확인 및 중복 체크
                if exercise_name not in VALID_EXERCISES_WITH_GIF or exercise_name in added_to_routine:
                    logger.warning(f"Invalid or duplicate exercise recommended by AI: {exercise_name}")
                    continue
                
                exercise_info = VALID_EXERCISES_WITH_GIF[exercise_name]
                added_to_routine.add(exercise_name)
                
                exercise, created = Exercise.objects.get_or_create(
                    name=exercise_name,
                    defaults={
                        'muscle_group': exercise_info['muscle_group'],
                        'gif_url': exercise_info['gif_url'],
                        'default_sets': exercise_data['sets'],
                        'default_reps': exercise_data['reps']
                    }
                )
                
                # 루틴에 운동 추가
                RoutineExercise.objects.create(
                    routine=routine,
                    exercise=exercise,
                    order=idx,
                    sets=exercise_data['sets'],
                    reps=exercise_data['reps'],
                    notes=EXERCISE_TIPS.get(exercise_name, DEFAULT_TIP)
                )
        
        serializer = RoutineSerializer(routine)
        return Response({
            'routine': serializer.data,
            'estimated_duration': routine_data.get('total_duration', data['duration'])
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"AI workout recommendation error: {str(e)}")
        
        # 에러 발생 시 기본 루틴 생성
        with transaction.atomic():
            routine_name = f"{muscle_group} {level} 기본 루틴"
            routine = Routine.objects.create(
                name=routine_name,
                level=data['level'],
                user=request.user,
                is_ai_generated=True
            )
            
            # 기본 세트/반복수 설정
            if level == "초급":
                sets, reps = 3, 12
            elif level == "중급":
                sets, reps = 4, 10
            else:
                sets, reps = 4, 8
            
            # 선택된 운동 추가
            for idx, exercise_name in enumerate(selected_exercises[:num_exercises]):
                if exercise_name in VALID_EXERCISES_WITH_GIF:
                    exercise_info = VALID_EXERCISES_WITH_GIF[exercise_name]
                    
                    exercise, created = Exercise.objects.get_or_create(
                        name=exercise_name,
                        defaults={
                            'muscle_group': exercise_info['muscle_group'],
                            'gif_url': exercise_info['gif_url'],
                            'default_sets': sets,
                            'default_reps': reps
                        }
                    )
                    
                    RoutineExercise.objects.create(
                        routine=routine,
                        exercise=exercise,
                        order=idx,
                        sets=sets,
                        reps=reps,
                        notes=EXERCISE_TIPS.get(exercise_name, DEFAULT_TIP)
                    )
        
        serializer = RoutineSerializer(routine)
        return Response({
            'routine': serializer.data,
            'estimated_duration': data['duration']
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def fitness_profile(request):
    """피트니스 프로필 조회 및 생성/수정"""
    if request.method == 'GET':
        try:
            profile = FitnessProfile.objects.get(user=request.user)
            serializer = FitnessProfileSerializer(profile)
            return Response(serializer.data)
        except FitnessProfile.DoesNotExist:
            # 프로필이 없으면 기본값으로 생성
            profile = FitnessProfile.objects.create(
                user=request.user,
                experience='beginner',
                goal='general_fitness',
                frequency=3,
                weight=70,
                height=170,
                gender='other'
            )
            serializer = FitnessProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    elif request.method == 'POST':
        # 기존 프로필이 있으면 업데이트, 없으면 생성
        profile, created = FitnessProfile.objects.get_or_create(user=request.user)
        serializer = FitnessProfileSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def workout_log_list(request):
    """운동 루틴 기록 목록 조회 및 생성"""
    if request.method == 'GET':
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        logs = WorkoutRoutineLog.objects.filter(user=request.user)
        
        if date_from:
            logs = logs.filter(date__gte=date_from)
        if date_to:
            logs = logs.filter(date__lte=date_to)
        
        serializer = WorkoutRoutineLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = WorkoutRoutineLogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def workout_log_detail(request, pk):
    """운동 루틴 기록 상세 조회, 수정, 삭제"""
    try:
        log = WorkoutRoutineLog.objects.get(pk=pk, user=request.user)
    except WorkoutRoutineLog.DoesNotExist:
        return Response(
            {"error": "운동 루틴 기록을 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = WorkoutRoutineLogSerializer(log)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = WorkoutRoutineLogSerializer(log, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        log.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
