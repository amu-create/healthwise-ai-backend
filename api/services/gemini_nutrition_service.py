"""
Gemini API를 활용한 영양 분석 서비스
"""
import os
import logging
import json
import random
from typing import Dict, List, Optional
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

class GeminiNutritionAnalyzer:
    """Gemini AI를 활용한 영양 분석 서비스"""
    
    def __init__(self):
        """Gemini API 초기화"""
        try:
            api_key = settings.GEMINI_API_KEY
            if not api_key or api_key == "your-gemini-api-key-here":
                logger.warning("Gemini API key not found, using fallback mode")
                self.model = None
                return
                
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini API initialized successfully")
            
        except Exception as e:
            logger.error(f"Gemini initialization failed: {str(e)}")
            self.model = None
    
    def analyze_food_with_ai(self, food_description: str, user_data: Optional[Dict] = None) -> Dict:
        """AI를 사용한 음식 영양 분석"""
        try:
            if not self.model:
                return self._fallback_analysis(food_description)
            
            # 사용자 정보 컨텍스트 생성
            user_context = ""
            if user_data:
                if user_data.get('allergies'):
                    user_context += f"알레르기: {', '.join(user_data['allergies'])}\n"
                if user_data.get('diseases'):
                    user_context += f"질병: {', '.join(user_data['diseases'])}\n"
                if user_data.get('fitness_goal'):
                    user_context += f"목표: {user_data['fitness_goal']}\n"
            
            # Gemini에게 영양 분석 요청
            prompt = f"""
            다음 음식에 대한 영양 정보를 분석해주세요.
            
            음식 설명: {food_description}
            {user_context}
            
            다음 형식의 JSON으로 답변해주세요:
            {{
                "food_items": [
                    {{
                        "name": "음식 이름",
                        "quantity": "예상 양 (g 또는 개수)",
                        "calories": 칼로리 (숫자),
                        "protein": 단백질g (숫자),
                        "carbs": 탄수화물g (숫자),
                        "fat": 지방g (숫자),
                        "fiber": 식이섬유g (숫자),
                        "sodium": 나트륨mg (숫자),
                        "sugar": 당류g (숫자)
                    }}
                ],
                "total_nutrition": {{
                    "calories": 총 칼로리,
                    "protein": 총 단백질,
                    "carbs": 총 탄수화물,
                    "fat": 총 지방,
                    "fiber": 총 식이섬유
                }},
                "health_assessment": {{
                    "score": 1-10 점수 (소수점 1자리),
                    "recommendations": ["추천사항1", "추천사항2"],
                    "warnings": ["주의사항"]
                }},
                "meal_suggestions": {{
                    "complement_foods": ["보충하면 좋은 음식"],
                    "next_meal_tips": "다음 식사 추천"
                }}
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # JSON 파싱
            content = response.text
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            
            # 결과 검증 및 보정
            result = self._validate_nutrition_data(result)
            
            return {
                'success': True,
                'analysis': result,
                'ai_powered': True
            }
            
        except Exception as e:
            logger.error(f"Gemini nutrition analysis failed: {str(e)}")
            return self._fallback_analysis(food_description)
    
    def suggest_meal_plan(self, user_data: Dict, meal_type: str = 'daily') -> Dict:
        """AI 기반 식단 추천"""
        try:
            if not self.model:
                return self._get_default_meal_plan(meal_type)
            
            # 사용자 정보 정리
            age = user_data.get('age', 30)
            gender = user_data.get('gender', '남성')
            weight = user_data.get('weight', 70)
            height = user_data.get('height', 170)
            activity_level = user_data.get('fitness_level', 'intermediate')
            goal = user_data.get('goal', '건강 유지')
            
            prompt = f"""
            다음 사용자를 위한 {meal_type} 식단을 추천해주세요.
            
            사용자 정보:
            - 나이: {age}세
            - 성별: {gender}
            - 체중: {weight}kg
            - 키: {height}cm
            - 활동 수준: {activity_level}
            - 목표: {goal}
            - 알레르기: {', '.join(user_data.get('allergies', [])) or '없음'}
            - 질병: {', '.join(user_data.get('diseases', [])) or '없음'}
            
            한국인이 쉽게 구할 수 있는 음식으로 추천해주세요.
            
            JSON 형식으로 답변:
            {{
                "meal_plan": {{
                    "breakfast": {{
                        "time": "07:00-08:00",
                        "foods": ["음식1", "음식2"],
                        "calories": 칼로리,
                        "preparation_tips": "조리 팁"
                    }},
                    "morning_snack": {{
                        "time": "10:00-10:30",
                        "foods": ["간식"],
                        "calories": 칼로리
                    }},
                    "lunch": {{
                        "time": "12:00-13:00",
                        "foods": ["음식1", "음식2", "음식3"],
                        "calories": 칼로리,
                        "preparation_tips": "조리 팁"
                    }},
                    "afternoon_snack": {{
                        "time": "15:00-15:30",
                        "foods": ["간식"],
                        "calories": 칼로리
                    }},
                    "dinner": {{
                        "time": "18:00-19:00",
                        "foods": ["음식1", "음식2", "음식3"],
                        "calories": 칼로리,
                        "preparation_tips": "조리 팁"
                    }}
                }},
                "daily_totals": {{
                    "calories": 총 칼로리,
                    "protein": 단백질g,
                    "carbs": 탄수화물g,
                    "fat": 지방g
                }},
                "shopping_list": ["재료1", "재료2", "재료3"],
                "meal_prep_tips": ["준비 팁1", "준비 팁2"]
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # JSON 파싱
            content = response.text
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            
            return {
                'success': True,
                'meal_plan': result,
                'ai_powered': True
            }
            
        except Exception as e:
            logger.error(f"Gemini meal plan generation failed: {str(e)}")
            return self._get_default_meal_plan(meal_type)
    
    def analyze_food_image(self, image_data: bytes) -> Dict:
        """음식 이미지 분석 (미래 기능)"""
        try:
            if not self.model:
                return {'error': 'Image analysis not available'}
            
            # Gemini Vision API 사용 (구현 예정)
            return {'error': 'Image analysis feature coming soon'}
            
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _validate_nutrition_data(self, data: Dict) -> Dict:
        """영양 데이터 검증 및 보정"""
        # 필수 필드 확인
        if 'food_items' not in data:
            data['food_items'] = []
        
        # 영양소 범위 검증
        for item in data.get('food_items', []):
            # 칼로리는 0-2000 범위
            if 'calories' in item:
                item['calories'] = max(0, min(2000, item['calories']))
            
            # 단백질, 탄수화물, 지방은 0-500g 범위
            for nutrient in ['protein', 'carbs', 'fat']:
                if nutrient in item:
                    item[nutrient] = max(0, min(500, item[nutrient]))
        
        # 총 영양소 재계산
        if 'total_nutrition' not in data:
            data['total_nutrition'] = {}
        
        total_calories = sum(item.get('calories', 0) for item in data['food_items'])
        total_protein = sum(item.get('protein', 0) for item in data['food_items'])
        total_carbs = sum(item.get('carbs', 0) for item in data['food_items'])
        total_fat = sum(item.get('fat', 0) for item in data['food_items'])
        total_fiber = sum(item.get('fiber', 0) for item in data['food_items'])
        
        data['total_nutrition'].update({
            'calories': total_calories,
            'protein': total_protein,
            'carbs': total_carbs,
            'fat': total_fat,
            'fiber': total_fiber
        })
        
        return data
    
    def _fallback_analysis(self, food_description: str) -> Dict:
        """폴백 영양 분석 (규칙 기반)"""
        # 음식별 기본 영양 정보 (100g 기준)
        food_db = {
            '삼겹살': {'calories': 300, 'protein': 17, 'carbs': 0, 'fat': 25, 'fiber': 0},
            '닭가슴살': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'fiber': 0},
            '현미밥': {'calories': 112, 'protein': 2.6, 'carbs': 23, 'fat': 0.9, 'fiber': 1.8},
            '백미밥': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3, 'fiber': 0.4},
            '브로콜리': {'calories': 34, 'protein': 2.8, 'carbs': 7, 'fat': 0.4, 'fiber': 2.6},
            '상추': {'calories': 15, 'protein': 1.4, 'carbs': 2.9, 'fat': 0.2, 'fiber': 1.3},
            '계란': {'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11, 'fiber': 0},
            '바나나': {'calories': 89, 'protein': 1.1, 'carbs': 23, 'fat': 0.3, 'fiber': 2.6},
            '오트밀': {'calories': 68, 'protein': 2.4, 'carbs': 12, 'fat': 1.4, 'fiber': 1.7},
            '연어': {'calories': 208, 'protein': 22, 'carbs': 0, 'fat': 13, 'fiber': 0},
            '두부': {'calories': 76, 'protein': 8, 'carbs': 1.9, 'fat': 4.8, 'fiber': 0.3},
            '아보카도': {'calories': 160, 'protein': 2, 'carbs': 9, 'fat': 15, 'fiber': 7},
            '김치': {'calories': 15, 'protein': 1.1, 'carbs': 2.4, 'fat': 0.5, 'fiber': 1.6},
            '요거트': {'calories': 59, 'protein': 3.5, 'carbs': 4.7, 'fat': 3.3, 'fiber': 0},
        }
        
        # 키워드 기반 음식 인식
        detected_foods = []
        food_lower = food_description.lower()
        
        for food_name, nutrition in food_db.items():
            if food_name in food_lower:
                quantity = random.randint(100, 200)  # 100g~200g
                detected_foods.append({
                    'name': food_name,
                    'quantity': f'{quantity}g',
                    'calories': int(nutrition['calories'] * quantity / 100),
                    'protein': round(nutrition['protein'] * quantity / 100, 1),
                    'carbs': round(nutrition['carbs'] * quantity / 100, 1),
                    'fat': round(nutrition['fat'] * quantity / 100, 1),
                    'fiber': round(nutrition['fiber'] * quantity / 100, 1),
                    'sodium': random.randint(100, 500),
                    'sugar': random.randint(2, 10)
                })
        
        # 인식된 음식이 없으면 기본값
        if not detected_foods:
            detected_foods = [{
                'name': '일반 음식',
                'quantity': '150g',
                'calories': random.randint(200, 400),
                'protein': random.randint(10, 25),
                'carbs': random.randint(20, 50),
                'fat': random.randint(5, 20),
                'fiber': random.randint(2, 5),
                'sodium': random.randint(200, 600),
                'sugar': random.randint(5, 15)
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
        warnings = []
        
        if total_nutrition['protein'] > 20:
            recommendations.append('단백질 함량이 적절합니다.')
            score += 0.5
        else:
            recommendations.append('단백질을 더 추가해보세요.')
            score -= 0.5
        
        if total_nutrition['fat'] > 40:
            warnings.append('지방 함량이 높습니다.')
            recommendations.append('다음 식사에서는 야채를 더 추가해보세요.')
            score -= 1.0
        
        if total_nutrition['fiber'] > 5:
            recommendations.append('식이섬유가 풍부합니다.')
            score += 0.5
        
        # 식사 제안
        complement_foods = []
        if total_nutrition['protein'] < 20:
            complement_foods.extend(['닭가슴살', '계란', '두부'])
        if total_nutrition['fiber'] < 5:
            complement_foods.extend(['브로콜리', '상추', '토마토'])
        
        return {
            'success': True,
            'analysis': {
                'food_items': detected_foods,
                'total_nutrition': total_nutrition,
                'health_assessment': {
                    'score': min(10, max(1, score)),
                    'recommendations': recommendations,
                    'warnings': warnings
                },
                'meal_suggestions': {
                    'complement_foods': complement_foods[:3],
                    'next_meal_tips': '균형 잡힌 영양소를 위해 다양한 색깔의 채소를 포함하세요.'
                }
            },
            'ai_powered': False
        }
    
    def _get_default_meal_plan(self, meal_type: str) -> Dict:
        """기본 식단 추천"""
        meal_plans = {
            'daily': {
                'meal_plan': {
                    'breakfast': {
                        'time': '07:00-08:00',
                        'foods': ['현미밥', '된장국', '계란말이', '김치'],
                        'calories': 450,
                        'preparation_tips': '현미밥은 전날 밤에 불려두면 더 부드럽게 지을 수 있습니다.'
                    },
                    'morning_snack': {
                        'time': '10:00-10:30',
                        'foods': ['사과 1개', '아몬드 10알'],
                        'calories': 150
                    },
                    'lunch': {
                        'time': '12:00-13:00',
                        'foods': ['잡곡밥', '닭가슴살 구이', '브로콜리', '시금치나물'],
                        'calories': 550,
                        'preparation_tips': '닭가슴살은 저염 간장에 재워두면 더 맛있습니다.'
                    },
                    'afternoon_snack': {
                        'time': '15:00-15:30',
                        'foods': ['그릭요거트', '블루베리'],
                        'calories': 120
                    },
                    'dinner': {
                        'time': '18:00-19:00',
                        'foods': ['현미밥', '연어구이', '아스파라거스', '샐러드'],
                        'calories': 500,
                        'preparation_tips': '연어는 레몬즙을 뿌려 구우면 비린내가 줄어듭니다.'
                    }
                },
                'daily_totals': {
                    'calories': 1770,
                    'protein': 125,
                    'carbs': 180,
                    'fat': 55
                },
                'shopping_list': [
                    '현미', '닭가슴살', '연어', '계란', '브로콜리',
                    '시금치', '아스파라거스', '사과', '블루베리',
                    '아몬드', '그릭요거트'
                ],
                'meal_prep_tips': [
                    '일요일에 일주일치 식단을 미리 계획하세요.',
                    '채소는 미리 손질해두면 조리 시간을 단축할 수 있습니다.'
                ]
            }
        }
        
        return {
            'success': True,
            'meal_plan': meal_plans.get(meal_type, meal_plans['daily']),
            'ai_powered': False
        }


# 전역 인스턴스
_gemini_analyzer = None

def get_gemini_analyzer() -> GeminiNutritionAnalyzer:
    """Gemini 분석기 인스턴스 가져오기 (싱글톤)"""
    global _gemini_analyzer
    if not _gemini_analyzer:
        _gemini_analyzer = GeminiNutritionAnalyzer()
    return _gemini_analyzer
