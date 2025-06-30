from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
import google.generativeai as genai
import json
import base64
import logging
from datetime import date, datetime, timedelta
from .models import FoodAnalysis, DailyNutrition
from apps.api.serializers.nutrition import (
    FoodAnalysisSerializer, FoodAnalysisRequestSerializer,
    DailyNutritionSerializer
)
from apps.core.models import UserProfile
from django.utils import translation

logger = logging.getLogger(__name__)

# Google Gemini API 설정
genai.configure(api_key=settings.GEMINI_API_KEY)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_nutrition_analysis_only(request):
    """AI 영양 분석만 수행 (저장하지 않음)"""
    serializer = FoodAnalysisRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # 사용자 프로필 가져오기
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    
    # 사용자 컨텍스트 생성
    user_context = ""
    if user_profile:
        age = date.today().year - user_profile.age
        user_context = f"""
        사용자 정보:
        - 나이: {age}세
        - 성별: {user_profile.gender}
        - 신장: {user_profile.height}cm
        - 체중: {user_profile.weight}kg
        - 질병: {', '.join(user_profile.diseases) if user_profile.diseases else '없음'}
        - 알레르기: {', '.join(user_profile.allergies) if user_profile.allergies else '없음'}
        """
    
    # 현재 언어 가져오기 (Accept-Language 헤더 또는 Django 설정)
    current_language = request.headers.get('Accept-Language', 'en')[:2]
    if current_language not in ['ko', 'en', 'es']:
        current_language = translation.get_language()[:2]  # Django 설정 사용
        if current_language not in ['ko', 'en', 'es']:
            current_language = 'en'  # 기본값
    
    # 언어별 프롬프트 템플릿
    prompts = {
        'ko': f"""
        다음 음식에 대해 영양 분석을 해주세요.
        
        {user_context}
        
        음식 정보:
        - 이름: {data.get('food_name', '제공된 이미지 참조')}
        - 설명: {data.get('description', '없음')}
        
        다음 정보를 JSON 형식으로 제공해주세요:
        {{
            "food_name": "음식 이름",
            "calories": 칼로리 (숫자),
            "protein": 단백질(g, 숫자),
            "carbohydrates": 탄수화물(g, 숫자),
            "fat": 지방(g, 숫자),
            "fiber": 식이섬유(g, 숫자, 선택),
            "sugar": 당류(g, 숫자, 선택),
            "sodium": 나트륨(mg, 숫자, 선택),
            "analysis_summary": "영양 성분 요약 (한국어로)",
            "recommendations": "이 사용자를 위한 섭취 권장사항 (한국어로)"
        }}
        
        주의사항:
        1. 이미지가 제공된 경우, 음식의 종류와 양을 추정하여 분석하세요.
        2. 사용자의 건강 상태를 고려한 맞춤형 권장사항을 제공하세요.
        3. 정확한 수치를 제공하기 어려운 경우, 일반적인 추정치를 사용하세요.
        4. 모든 설명은 한국어로 작성하세요.
        """,
        'en': f"""
        Please analyze the nutrition of the following food.
        
        User Information:
        - Age: {user_profile.age if user_profile else 'Unknown'} years
        - Gender: {user_profile.gender if user_profile else 'Unknown'}
        - Height: {user_profile.height if user_profile else 'Unknown'}cm
        - Weight: {user_profile.weight if user_profile else 'Unknown'}kg
        - Diseases: {', '.join(user_profile.diseases) if user_profile and user_profile.diseases else 'None'}
        - Allergies: {', '.join(user_profile.allergies) if user_profile and user_profile.allergies else 'None'}
        
        Food Information:
        - Name: {data.get('food_name', 'Refer to provided image')}
        - Description: {data.get('description', 'None')}
        
        Please provide the following information in JSON format:
        {{
            "food_name": "Food name",
            "calories": Calories (number),
            "protein": Protein(g, number),
            "carbohydrates": Carbohydrates(g, number),
            "fat": Fat(g, number),
            "fiber": Dietary fiber(g, number, optional),
            "sugar": Sugar(g, number, optional),
            "sodium": Sodium(mg, number, optional),
            "analysis_summary": "Nutritional summary (in English)",
            "recommendations": "Intake recommendations for this user (in English)"
        }}
        
        Note:
        1. If an image is provided, estimate the type and amount of food for analysis.
        2. Provide personalized recommendations considering the user's health condition.
        3. Use general estimates if exact figures are difficult to provide.
        4. Write all descriptions in English.
        """,
        'es': f"""
        Por favor analiza la nutrición de la siguiente comida.
        
        Información del usuario:
        - Edad: {user_profile.age if user_profile else 'Desconocido'} años
        - Género: {user_profile.gender if user_profile else 'Desconocido'}
        - Altura: {user_profile.height if user_profile else 'Desconocido'}cm
        - Peso: {user_profile.weight if user_profile else 'Desconocido'}kg
        - Enfermedades: {', '.join(user_profile.diseases) if user_profile and user_profile.diseases else 'Ninguna'}
        - Alergias: {', '.join(user_profile.allergies) if user_profile and user_profile.allergies else 'Ninguna'}
        
        Información de la comida:
        - Nombre: {data.get('food_name', 'Consultar imagen proporcionada')}
        - Descripción: {data.get('description', 'Ninguna')}
        
        Por favor proporciona la siguiente información en formato JSON:
        {{
            "food_name": "Nombre de la comida",
            "calories": Calorías (número),
            "protein": Proteína(g, número),
            "carbohydrates": Carbohidratos(g, número),
            "fat": Grasa(g, número),
            "fiber": Fibra dietética(g, número, opcional),
            "sugar": Azúcar(g, número, opcional),
            "sodium": Sodio(mg, número, opcional),
            "analysis_summary": "Resumen nutricional (en español)",
            "recommendations": "Recomendaciones de consumo para este usuario (en español)"
        }}
        
        Nota:
        1. Si se proporciona una imagen, estima el tipo y cantidad de comida para el análisis.
        2. Proporciona recomendaciones personalizadas considerando la condición de salud del usuario.
        3. Usa estimaciones generales si es difícil proporcionar cifras exactas.
        4. Escribe todas las descripciones en español.
        """
    }
    
    # 프롬프트 선택 (기본값: 영어)
    prompt = prompts.get(current_language, prompts['en'])
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash' if data.get('image_base64') else 'gemini-1.5-flash')
        
        # 이미지가 있는 경우
        if data.get('image_base64'):
            # base64 디코딩
            image_data = base64.b64decode(data['image_base64'].split(',')[1] if ',' in data['image_base64'] else data['image_base64'])
            
            response = model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])
        else:
            response = model.generate_content(prompt)
        
        # 응답 파싱
        response_text = response.text
        # JSON 블록 추출
        if '```json' in response_text:
            json_str = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            json_str = response_text.split('```')[1].strip()
        else:
            json_str = response_text.strip()
        
        nutrition_data = json.loads(json_str)
        
        # 분석 결과만 반환 (저장하지 않음)
        return Response({
            'food_name': nutrition_data['food_name'],
            'calories': nutrition_data['calories'],
            'protein': nutrition_data['protein'],
            'carbohydrates': nutrition_data['carbohydrates'],
            'fat': nutrition_data['fat'],
            'fiber': nutrition_data.get('fiber', 0),
            'sugar': nutrition_data.get('sugar', 0),
            'sodium': nutrition_data.get('sodium', 0),
            'analysis_summary': nutrition_data['analysis_summary'],
            'recommendations': nutrition_data['recommendations']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"AI nutrition analysis error: {str(e)}")
        return Response(
            {"error": f"영양 분석 중 오류가 발생했습니다: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_nutrition_analysis(request):
    """AI 영양 분석"""
    serializer = FoodAnalysisRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # 사용자 프로필 가져오기
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    
    # 사용자 컨텍스트 생성
    user_context = ""
    if user_profile:
        age = date.today().year - user_profile.age
        user_context = f"""
        사용자 정보:
        - 나이: {age}세
        - 성별: {user_profile.gender}
        - 신장: {user_profile.height}cm
        - 체중: {user_profile.weight}kg
        - 질병: {', '.join(user_profile.diseases) if user_profile.diseases else '없음'}
        - 알레르기: {', '.join(user_profile.allergies) if user_profile.allergies else '없음'}
        """
    
    # 현재 언어 가져오기 (Accept-Language 헤더 또는 Django 설정)
    current_language = request.headers.get('Accept-Language', 'en')[:2]
    if current_language not in ['ko', 'en', 'es']:
        current_language = translation.get_language()[:2]  # Django 설정 사용
        if current_language not in ['ko', 'en', 'es']:
            current_language = 'en'  # 기본값
    
    # 언어별 프롬프트 템플릿
    prompts = {
        'ko': f"""
        다음 음식에 대해 영양 분석을 해주세요.
        
        {user_context}
        
        음식 정보:
        - 이름: {data.get('food_name', '제공된 이미지 참조')}
        - 설명: {data.get('description', '없음')}
        
        다음 정보를 JSON 형식으로 제공해주세요:
        {{
            "food_name": "음식 이름",
            "calories": 칼로리 (숫자),
            "protein": 단백질(g, 숫자),
            "carbohydrates": 탄수화물(g, 숫자),
            "fat": 지방(g, 숫자),
            "fiber": 식이섬유(g, 숫자, 선택),
            "sugar": 당류(g, 숫자, 선택),
            "sodium": 나트륨(mg, 숫자, 선택),
            "analysis_summary": "영양 성분 요약 (한국어로)",
            "recommendations": "이 사용자를 위한 섭취 권장사항 (한국어로)"
        }}
        
        주의사항:
        1. 이미지가 제공된 경우, 음식의 종류와 양을 추정하여 분석하세요.
        2. 사용자의 건강 상태를 고려한 맞춤형 권장사항을 제공하세요.
        3. 정확한 수치를 제공하기 어려운 경우, 일반적인 추정치를 사용하세요.
        4. 모든 설명은 한국어로 작성하세요.
        """,
        'en': f"""
        Please analyze the nutrition of the following food.
        
        User Information:
        - Age: {user_profile.age if user_profile else 'Unknown'} years
        - Gender: {user_profile.gender if user_profile else 'Unknown'}
        - Height: {user_profile.height if user_profile else 'Unknown'}cm
        - Weight: {user_profile.weight if user_profile else 'Unknown'}kg
        - Diseases: {', '.join(user_profile.diseases) if user_profile and user_profile.diseases else 'None'}
        - Allergies: {', '.join(user_profile.allergies) if user_profile and user_profile.allergies else 'None'}
        
        Food Information:
        - Name: {data.get('food_name', 'Refer to provided image')}
        - Description: {data.get('description', 'None')}
        
        Please provide the following information in JSON format:
        {{
            "food_name": "Food name",
            "calories": Calories (number),
            "protein": Protein(g, number),
            "carbohydrates": Carbohydrates(g, number),
            "fat": Fat(g, number),
            "fiber": Dietary fiber(g, number, optional),
            "sugar": Sugar(g, number, optional),
            "sodium": Sodium(mg, number, optional),
            "analysis_summary": "Nutritional summary (in English)",
            "recommendations": "Intake recommendations for this user (in English)"
        }}
        
        Note:
        1. If an image is provided, estimate the type and amount of food for analysis.
        2. Provide personalized recommendations considering the user's health condition.
        3. Use general estimates if exact figures are difficult to provide.
        4. Write all descriptions in English.
        """,
        'es': f"""
        Por favor analiza la nutrición de la siguiente comida.
        
        Información del usuario:
        - Edad: {user_profile.age if user_profile else 'Desconocido'} años
        - Género: {user_profile.gender if user_profile else 'Desconocido'}
        - Altura: {user_profile.height if user_profile else 'Desconocido'}cm
        - Peso: {user_profile.weight if user_profile else 'Desconocido'}kg
        - Enfermedades: {', '.join(user_profile.diseases) if user_profile and user_profile.diseases else 'Ninguna'}
        - Alergias: {', '.join(user_profile.allergies) if user_profile and user_profile.allergies else 'Ninguna'}
        
        Información de la comida:
        - Nombre: {data.get('food_name', 'Consultar imagen proporcionada')}
        - Descripción: {data.get('description', 'Ninguna')}
        
        Por favor proporciona la siguiente información en formato JSON:
        {{
            "food_name": "Nombre de la comida",
            "calories": Calorías (número),
            "protein": Proteína(g, número),
            "carbohydrates": Carbohidratos(g, número),
            "fat": Grasa(g, número),
            "fiber": Fibra dietética(g, número, opcional),
            "sugar": Azúcar(g, número, opcional),
            "sodium": Sodio(mg, número, opcional),
            "analysis_summary": "Resumen nutricional (en español)",
            "recommendations": "Recomendaciones de consumo para este usuario (en español)"
        }}
        
        Nota:
        1. Si se proporciona una imagen, estima el tipo y cantidad de comida para el análisis.
        2. Proporciona recomendaciones personalizadas considerando la condición de salud del usuario.
        3. Usa estimaciones generales si es difícil proporcionar cifras exactas.
        4. Escribe todas las descripciones en español.
        """
    }
    
    # 프롬프트 선택 (기본값: 영어)
    prompt = prompts.get(current_language, prompts['en'])
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash' if data.get('image_base64') else 'gemini-1.5-flash')
        
        # 이미지가 있는 경우
        if data.get('image_base64'):
            # base64 디코딩
            image_data = base64.b64decode(data['image_base64'].split(',')[1] if ',' in data['image_base64'] else data['image_base64'])
            
            response = model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])
        else:
            response = model.generate_content(prompt)
        
        # 응답 파싱
        response_text = response.text
        # JSON 블록 추출
        if '```json' in response_text:
            json_str = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            json_str = response_text.split('```')[1].strip()
        else:
            json_str = response_text.strip()
        
        nutrition_data = json.loads(json_str)
        
        # FoodAnalysis 객체 생성
        food_analysis = FoodAnalysis.objects.create(
            user=request.user,
            food_name=nutrition_data['food_name'],
            description=data.get('description', ''),
            image_base64=data.get('image_base64', ''),
            calories=nutrition_data['calories'],
            protein=nutrition_data['protein'],
            carbohydrates=nutrition_data['carbohydrates'],
            fat=nutrition_data['fat'],
            fiber=nutrition_data.get('fiber', 0),
            sugar=nutrition_data.get('sugar', 0),
            sodium=nutrition_data.get('sodium', 0),
            analysis_summary=nutrition_data['analysis_summary'],
            recommendations=nutrition_data['recommendations']
        )
        
        # 오늘의 영양 기록에 추가
        today = date.today()
        daily_nutrition, created = DailyNutrition.objects.get_or_create(
            user=request.user,
            date=today
        )
        daily_nutrition.food_analyses.add(food_analysis)
        
        # 총 영양소 업데이트
        daily_nutrition.total_calories = daily_nutrition.food_analyses.aggregate(
            total=Sum('calories')
        )['total'] or 0
        daily_nutrition.total_protein = daily_nutrition.food_analyses.aggregate(
            total=Sum('protein')
        )['total'] or 0
        daily_nutrition.total_carbohydrates = daily_nutrition.food_analyses.aggregate(
            total=Sum('carbohydrates')
        )['total'] or 0
        daily_nutrition.total_fat = daily_nutrition.food_analyses.aggregate(
            total=Sum('fat')
        )['total'] or 0
        daily_nutrition.save()
        
        serializer = FoodAnalysisSerializer(food_analysis)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"AI nutrition analysis error: {str(e)}")
        return Response(
            {"error": f"영양 분석 중 오류가 발생했습니다: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def food_analysis_list(request):
    """음식 분석 기록 목록 조회"""
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    
    analyses = FoodAnalysis.objects.filter(user=request.user)
    
    if date_from:
        analyses = analyses.filter(analyzed_at__date__gte=date_from)
    if date_to:
        analyses = analyses.filter(analyzed_at__date__lte=date_to)
    
    serializer = FoodAnalysisSerializer(analyses, many=True)
    return Response(serializer.data)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def food_analysis_detail(request, pk):
    """음식 분석 기록 상세 조회 및 삭제"""
    try:
        analysis = FoodAnalysis.objects.get(pk=pk, user=request.user)
    except FoodAnalysis.DoesNotExist:
        return Response(
            {"error": "음식 분석 기록을 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = FoodAnalysisSerializer(analysis)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        # 일일 영양 기록에서도 제거
        daily_nutritions = analysis.dailynutrition_set.all()
        for dn in daily_nutritions:
            dn.food_analyses.remove(analysis)
            # 총 영양소 재계산
            dn.total_calories = dn.food_analyses.aggregate(
                total=Sum('calories')
            )['total'] or 0
            dn.total_protein = dn.food_analyses.aggregate(
                total=Sum('protein')
            )['total'] or 0
            dn.total_carbohydrates = dn.food_analyses.aggregate(
                total=Sum('carbohydrates')
            )['total'] or 0
            dn.total_fat = dn.food_analyses.aggregate(
                total=Sum('fat')
            )['total'] or 0
            dn.save()
        
        analysis.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_nutrition_list(request):
    """일일 영양 기록 목록 조회"""
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    
    records = DailyNutrition.objects.filter(user=request.user)
    
    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)
    
    serializer = DailyNutritionSerializer(records, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_nutrition_detail(request, date_str):
    """특정 날짜의 영양 기록 조회"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {"error": "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        record = DailyNutrition.objects.get(user=request.user, date=target_date)
        serializer = DailyNutritionSerializer(record)
        return Response(serializer.data)
    except DailyNutrition.DoesNotExist:
        return Response(
            {"error": "해당 날짜의 영양 기록이 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nutrition_statistics(request):
    """영양 통계 조회"""
    # 날짜 파라미터로 기간 설정
    start_date_str = request.query_params.get('start_date')
    end_date_str = request.query_params.get('end_date')
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        # 기본값: 최근 7일
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
    
    # 모든 날짜 범위의 기록 조회
    records = DailyNutrition.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    # 통계 계산
    total_calories = records.aggregate(Sum('total_calories'))['total_calories__sum'] or 0
    total_protein = records.aggregate(Sum('total_protein'))['total_protein__sum'] or 0
    total_carbs = records.aggregate(Sum('total_carbohydrates'))['total_carbohydrates__sum'] or 0
    total_fat = records.aggregate(Sum('total_fat'))['total_fat__sum'] or 0
    
    # 기록이 있는 일수
    recorded_days = records.count()
    days = (end_date - start_date).days + 1
    
    # 평균 계산 (기록이 있는 날짜 기준)
    avg_calories = total_calories / recorded_days if recorded_days > 0 else 0
    avg_protein = total_protein / recorded_days if recorded_days > 0 else 0
    avg_carbs = total_carbs / recorded_days if recorded_days > 0 else 0
    avg_fat = total_fat / recorded_days if recorded_days > 0 else 0
    
    # 이전 기간 대비 변화율 계산
    prev_period_days = days
    prev_start_date = start_date - timedelta(days=prev_period_days)
    prev_end_date = start_date - timedelta(days=1)
    
    prev_records = DailyNutrition.objects.filter(
        user=request.user,
        date__range=[prev_start_date, prev_end_date]
    )
    
    prev_total_calories = prev_records.aggregate(Sum('total_calories'))['total_calories__sum'] or 0
    prev_total_protein = prev_records.aggregate(Sum('total_protein'))['total_protein__sum'] or 0
    prev_total_carbs = prev_records.aggregate(Sum('total_carbohydrates'))['total_carbohydrates__sum'] or 0
    prev_total_fat = prev_records.aggregate(Sum('total_fat'))['total_fat__sum'] or 0
    
    prev_recorded_days = prev_records.count()
    
    # 변화율 계산
    def calculate_trend(current, previous, prev_days):
        if prev_days > 0 and previous > 0:
            prev_avg = previous / prev_days
            return ((current / recorded_days if recorded_days > 0 else 0) - prev_avg) / prev_avg * 100
        return 0
    
    trend_calories = calculate_trend(total_calories, prev_total_calories, prev_recorded_days)
    trend_protein = calculate_trend(total_protein, prev_total_protein, prev_recorded_days)
    trend_carbs = calculate_trend(total_carbs, prev_total_carbs, prev_recorded_days)
    trend_fat = calculate_trend(total_fat, prev_total_fat, prev_recorded_days)
    
    # 일별 데이터 및 음식 개수
    daily_data = []
    total_analyses = 0
    
    # 모든 날짜를 포함하여 데이터 생성
    current_date = start_date
    while current_date <= end_date:
        record = records.filter(date=current_date).first()
        if record:
            food_count = record.food_analyses.count()
            total_analyses += food_count
            daily_data.append({
                'date': current_date.isoformat(),
                'total_calories': record.total_calories,
                'total_protein': record.total_protein,
                'total_carbohydrates': record.total_carbohydrates,
                'total_fat': record.total_fat,
                'food_count': food_count
            })
        else:
            # 기록이 없는 날도 0으로 포함
            daily_data.append({
                'date': current_date.isoformat(),
                'total_calories': 0,
                'total_protein': 0,
                'total_carbohydrates': 0,
                'total_fat': 0,
                'food_count': 0
            })
        current_date += timedelta(days=1)
    
    return Response({
        'daily_data': daily_data,
        'period_stats': {
            'average_calories': round(avg_calories, 1),
            'average_protein': round(avg_protein, 1),
            'average_carbohydrates': round(avg_carbs, 1),
            'average_fat': round(avg_fat, 1),
            'total_days': days,
            'total_analyses': total_analyses,
            'trend_calories': round(trend_calories, 1),
            'trend_protein': round(trend_protein, 1),
            'trend_carbohydrates': round(trend_carbs, 1),
            'trend_fat': round(trend_fat, 1)
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nutrition_complete(request):
    """임시 분석 결과를 영구 저장"""
    try:
        # request body에서 분석 데이터 추출
        data = request.data
        
        # FoodAnalysis 객체 생성
        food_analysis = FoodAnalysis.objects.create(
            user=request.user,
            food_name=data.get('food_name', ''),
            description=data.get('description', ''),
            image_base64=data.get('image_base64', ''),
            calories=data.get('calories', 0),
            protein=data.get('protein', 0),
            carbohydrates=data.get('carbohydrates', 0),
            fat=data.get('fat', 0),
            fiber=data.get('fiber', 0),
            sugar=data.get('sugar', 0),
            sodium=data.get('sodium', 0),
            analysis_summary=data.get('analysis_summary', ''),
            recommendations=data.get('recommendations', '')
        )
        
        # 오늘의 영양 기록에 추가
        today = date.today()
        daily_nutrition, created = DailyNutrition.objects.get_or_create(
            user=request.user,
            date=today
        )
        daily_nutrition.food_analyses.add(food_analysis)
        
        # 총 영양소 업데이트
        daily_nutrition.total_calories = daily_nutrition.food_analyses.aggregate(
            total=Sum('calories')
        )['total'] or 0
        daily_nutrition.total_protein = daily_nutrition.food_analyses.aggregate(
            total=Sum('protein')
        )['total'] or 0
        daily_nutrition.total_carbohydrates = daily_nutrition.food_analyses.aggregate(
            total=Sum('carbohydrates')
        )['total'] or 0
        daily_nutrition.total_fat = daily_nutrition.food_analyses.aggregate(
            total=Sum('fat')
        )['total'] or 0
        daily_nutrition.save()
        
        serializer = FoodAnalysisSerializer(food_analysis)
        return Response({
            'success': True,
            'message': '영양 정보가 성공적으로 저장되었습니다.',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Nutrition complete error: {str(e)}")
        return Response(
            {"error": f"영양 정보 저장 중 오류가 발생했습니다: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )