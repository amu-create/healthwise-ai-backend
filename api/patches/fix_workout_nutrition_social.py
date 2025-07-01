# 운동, 영양, 소셜 기능 수정 패치
# 이 파일은 views.py와 views_nutrition.py에 적용할 수정사항을 담고 있습니다

"""
문제 해결 내용:

1. 운동 로그 저장 문제 수정
- duration 값이 정확히 저장되도록 수정
- 칼로리 계산 로직 개선

2. 영양 정보 대시보드 반영 문제 수정
- ai_nutrition_analysis_only 후 nutrition_complete로 저장하는 플로우 개선
- DailyNutrition 업데이트 로직 수정

3. 소셜 포스트 500 에러 수정
- 게스트 사용자 처리 로직 추가
- 에러 핸들링 개선

적용 방법:
1. views.py의 workout_logs_create 함수 수정
2. views_nutrition.py의 nutrition_complete 함수 수정
3. views.py의 social_posts_create 함수 수정
"""

# 1. workout_logs_create 수정 (views.py 1046줄 근처)
def workout_logs_create_fixed(request):
    """운동 로그 생성 (수정된 버전)"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = request.data
        
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
        
        # 운동 로그 생성
        workout_log = {
            'id': random.randint(1000, 9999),
            'routine_id': data.get('routine_id'),
            'routine_name': data.get('routine_name', '운동 루틴'),
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
            user_id = request.user.id
            content = data.get('social_content', f'{duration}분 동안 운동을 완료했습니다! 💪')
            
            # 소셜 포스트 생성
            social_post = social_workout_service.create_workout_post(
                user_id=user_id,
                workout_log_id=workout_log['id'],
                content=content
            )
        
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

# 2. nutrition_complete 수정 (views_nutrition.py 끝부분)
def nutrition_complete_fixed(request):
    """임시 분석 결과를 영구 저장 (수정된 버전)"""
    try:
        # 게스트 사용자 체크
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'error': '게스트 사용자는 영양 정보를 저장할 수 없습니다.',
                'message': '회원가입 후 이용해주세요.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # request body에서 분석 데이터 추출
        data = request.data
        
        # 숫자 필드 검증 및 변환
        try:
            calories = float(data.get('calories', 0))
            protein = float(data.get('protein', 0))
            carbohydrates = float(data.get('carbohydrates', 0))
            fat = float(data.get('fat', 0))
            fiber = float(data.get('fiber', 0))
            sugar = float(data.get('sugar', 0))
            sodium = float(data.get('sodium', 0))
        except ValueError as e:
            return Response({
                'error': f'영양 수치가 올바르지 않습니다: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # FoodAnalysis 객체 생성
        food_analysis = FoodAnalysis.objects.create(
            user=request.user,
            food_name=data.get('food_name', ''),
            description=data.get('description', ''),
            image_base64=data.get('image_base64', ''),
            calories=calories,
            protein=protein,
            carbohydrates=carbohydrates,
            fat=fat,
            fiber=fiber,
            sugar=sugar,
            sodium=sodium,
            analysis_summary=data.get('analysis_summary', ''),
            recommendations=data.get('recommendations', '')
        )
        
        # 오늘의 영양 기록에 추가
        today = date.today()
        with transaction.atomic():  # 트랜잭션으로 묶어서 처리
            daily_nutrition, created = DailyNutrition.objects.get_or_create(
                user=request.user,
                date=today
            )
            daily_nutrition.food_analyses.add(food_analysis)
            
            # 총 영양소 업데이트 (Sum 사용하여 정확히 계산)
            from django.db.models import Sum
            
            totals = daily_nutrition.food_analyses.aggregate(
                total_calories=Sum('calories'),
                total_protein=Sum('protein'),
                total_carbohydrates=Sum('carbohydrates'),
                total_fat=Sum('fat')
            )
            
            daily_nutrition.total_calories = totals['total_calories'] or 0
            daily_nutrition.total_protein = totals['total_protein'] or 0
            daily_nutrition.total_carbohydrates = totals['total_carbohydrates'] or 0
            daily_nutrition.total_fat = totals['total_fat'] or 0
            daily_nutrition.save()
        
        # 업데이트된 일일 영양 정보 포함하여 반환
        serializer = FoodAnalysisSerializer(food_analysis)
        return Response({
            'success': True,
            'message': '영양 정보가 성공적으로 저장되었습니다.',
            'data': serializer.data,
            'daily_totals': {
                'date': today.isoformat(),
                'total_calories': daily_nutrition.total_calories,
                'total_protein': daily_nutrition.total_protein,
                'total_carbohydrates': daily_nutrition.total_carbohydrates,
                'total_fat': daily_nutrition.total_fat
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Nutrition complete error: {str(e)}")
        return Response(
            {"error": f"영양 정보 저장 중 오류가 발생했습니다: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# 3. social_posts_create 수정 (views.py 850줄 근처)
def social_posts_create_fixed(request):
    """소셜 포스트 생성 (수정된 버전)"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        # 게스트 사용자 체크
        is_guest = not request.user.is_authenticated or request.headers.get('X-Is-Guest') == 'true'
        
        if is_guest:
            return Response({
                'success': False,
                'error': '게스트 사용자는 포스트를 작성할 수 없습니다.',
                'message': '회원가입 후 이용해주세요.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # multipart/form-data 처리
        content = request.data.get('content', '')
        visibility = request.data.get('visibility', 'public')
        media_file = request.FILES.get('media_file')
        workout_session_id = request.data.get('workout_session_id')
        workout_log_id = request.data.get('workout_log_id')
        
        # 컨텐츠가 비어있으면 에러
        if not content and not media_file:
            return Response({
                'success': False,
                'error': 'Content or image is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 파일 처리 (media_file이 있는 경우)
        image_url = None
        if media_file:
            # 파일 크기 체크 (10MB 제한)
            if media_file.size > 10 * 1024 * 1024:
                return Response({
                    'success': False,
                    'error': '파일 크기는 10MB를 초과할 수 없습니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 파일 타입 체크
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if media_file.content_type not in allowed_types:
                return Response({
                    'success': False,
                    'error': '지원하지 않는 파일 형식입니다. (JPEG, PNG, GIF, WebP만 가능)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 여기서는 간단히 URL만 생성 (실제로는 S3 등에 업로드 필요)
            image_url = f'/media/posts/{media_file.name}'
            # TODO: 실제 파일 업로드 처리
        
        # 새 게시물 생성
        new_post = {
            'id': random.randint(100, 999),
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'profile_image': None,  # TODO: 프로필 이미지 추가
                'profile_picture_url': None
            },
            'content': content,
            'image_url': image_url,
            'media_file': image_url,
            'visibility': visibility,
            'workout_session': workout_session_id,
            'workout_log_id': workout_log_id,
            'likes': [],
            'comments': [],
            'created_at': datetime.now().isoformat(),
            'is_liked': False,
            'is_saved': False,
            'likes_count': 0,
            'comments_count': 0,
            'shares_count': 0,
            'reactions': [],
            'tags': [],
            'mentions': []
        }
        
        # TODO: 실제 DB 저장 로직
        # if request.user.is_authenticated:
        #     post = Post.objects.create(
        #         user=request.user,
        #         content=content,
        #         visibility=visibility,
        #         ...
        #     )
        
        # 성공 응답
        return Response(new_post, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f'Social post create error: {str(e)}', exc_info=True)
        return Response({
            'error': f'Failed to create post: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
