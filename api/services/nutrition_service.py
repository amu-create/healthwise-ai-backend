import random

def analyze_food_simple(food_description):
    """간단한 음식 분석 (AI 대신 룰 베이스)"""
    
    # 음식별 기본 영양 정보 (100g 기준)
    food_db = {
        '삼겹살': {'calories': 300, 'protein': 17, 'carbs': 0, 'fat': 25},
        '닭가슴살': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6},
        '현미밥': {'calories': 112, 'protein': 2.6, 'carbs': 23, 'fat': 0.9},
        '백미밥': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3},
        '브로콜리': {'calories': 34, 'protein': 2.8, 'carbs': 7, 'fat': 0.4},
        '상추': {'calories': 15, 'protein': 1.4, 'carbs': 2.9, 'fat': 0.2},
        '계란': {'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11},
        '바나나': {'calories': 89, 'protein': 1.1, 'carbs': 23, 'fat': 0.3},
        '오트밀': {'calories': 68, 'protein': 2.4, 'carbs': 12, 'fat': 1.4},
    }
    
    # 키워드 기반 음식 인식
    detected_foods = []
    for food_name, nutrition in food_db.items():
        if food_name in food_description:
            quantity = random.randint(80, 200)  # 80g~200g
            detected_foods.append({
                'name': food_name,
                'quantity': f'{quantity}g',
                'calories': int(nutrition['calories'] * quantity / 100),
                'protein': round(nutrition['protein'] * quantity / 100, 1),
                'carbs': round(nutrition['carbs'] * quantity / 100, 1),
                'fat': round(nutrition['fat'] * quantity / 100, 1),
                'fiber': random.randint(1, 5),
                'confidence': random.uniform(0.8, 0.95)
            })
    
    # 인식된 음식이 없으면 기본값
    if not detected_foods:
        detected_foods = [{
            'name': '일반 음식',
            'quantity': '150g',
            'calories': random.randint(200, 500),
            'protein': random.randint(10, 30),
            'carbs': random.randint(20, 60),
            'fat': random.randint(5, 25),
            'fiber': random.randint(2, 8),
            'confidence': 0.7
        }]
    
    # 총 영양소 계산
    total_nutrition = {
        'calories': sum(food['calories'] for food in detected_foods),
        'protein': sum(food['protein'] for food in detected_foods),
        'carbs': sum(food['carbs'] for food in detected_foods),
        'fat': sum(food['fat'] for food in detected_foods),
        'fiber': sum(food['fiber'] for food in detected_foods)
    }
    
    # 건강 평가
    score = 7.0
    recommendations = []
    
    if total_nutrition['protein'] > 20:
        recommendations.append('단백질 함량이 적절합니다')
        score += 0.5
    else:
        recommendations.append('단백질을 더 추가해보세요')
        score -= 0.5
    
    if total_nutrition['fat'] > 30:
        recommendations.append('지방 함량이 높으니 다음 식사에서는 야채를 더 추가해보세요')
        score -= 1.0
    
    if total_nutrition['fiber'] > 3:
        recommendations.append('식이섬유가 풍부합니다')
        score += 0.5
    
    recommendations.append('전체적으로 균형잡힌 식사입니다')
    
    return {
        'food_items': detected_foods,
        'total_nutrition': total_nutrition,
        'health_assessment': {
            'score': min(10, max(1, score)),
            'recommendations': recommendations
        }
    }

def get_nutrition_mock_data(date):
    """Mock 영양 데이터 생성"""
    return {
        'date': date,
        'daily_goal': {
            'calories': 2000,
            'protein': 150,
            'carbs': 250,
            'fat': 65,
            'fiber': 25
        },
        'consumed': {
            'calories': random.randint(1500, 1800),
            'protein': random.randint(100, 140),
            'carbs': random.randint(150, 200),
            'fat': random.randint(45, 60),
            'fiber': random.randint(15, 22)
        },
        'meals': [
            {
                'type': 'breakfast',
                'time': '08:00',
                'foods': ['오트밀', '바나나', '아몬드'],
                'calories': random.randint(300, 400)
            },
            {
                'type': 'lunch',
                'time': '12:30',
                'foods': ['현미밥', '닭가슴살', '브로콜리'],
                'calories': random.randint(450, 550)
            },
            {
                'type': 'dinner',
                'time': '19:00',
                'foods': ['연어구이', '퀴노아', '아스파라거스'],
                'calories': random.randint(400, 500)
            }
        ]
    }
