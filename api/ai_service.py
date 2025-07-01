"""
AI 챗봇 서비스 - 원본 프로젝트 기반 간소화 버전
"""
import os
import logging
import time
from typing import Dict, List, Optional
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from openai import OpenAI
import json
from datetime import datetime, timedelta, date
import hashlib
# Railway 배포를 위해 무거운 라이브러리 조건부 import
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    VECTORSTORE_AVAILABLE = True
except ImportError:
    logger.warning("VectorStore libraries not available. Running without embeddings.")
    VECTORSTORE_AVAILABLE = False
import numpy as np

logger = logging.getLogger(__name__)

class HealthAIChatbot:
    """헬스케어 AI 챗봇 - Railway 배포용 경량화 버전"""
    
    # 클래스 변수로 벡터스토어 공유
    _embeddings = None
    _vectorstore = None
    
    def __init__(self):
        try:
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OpenAI API key not found")
                
            self.client = OpenAI(api_key=api_key)
            
            # 캐시 설정
            self.cache_timeout = 3600  # 1시간
            
            # 카테고리 키워드 정의
            self.category_keywords = {
                'exercise': ['운동', '스쿼트', '푸시업', '플랭크', '런닝', '요가', '필라테스', '근육', '체력', '트레이닝'],
                'nutrition': ['영양', '단백질', '탄수화물', '지방', '비타민', '칼로리', '식단', '음식', '다이어트', '식품'],
                'health': ['건강', '질병', '증상', '치료', '예방', '면역', '스트레스', '수면', '정신건강', '의학']
            }
            
            # 벡터스토어 초기화 (필요시)
            if VECTORSTORE_AVAILABLE and not HealthAIChatbot._embeddings:
                self._initialize_vectorstore()
            
            logger.info("HealthAIChatbot initialized successfully")
            
        except Exception as e:
            logger.error(f"HealthAIChatbot initialization failed: {str(e)}")
            raise
    
    @classmethod
    def _initialize_vectorstore(cls):
        """벡터스토어 초기화 - 한 번만 실행"""
        try:
            logger.info("Initializing vectorstore...")
            
            # HuggingFace 임베딩 모델 (무료)
            cls._embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={"device": "cpu"},  # Railway는 CPU 사용
                encode_kwargs={'normalize_embeddings': True}
            )
            
            # 벡터스토어 경로 확인
            vectorstore_path = os.path.join(settings.BASE_DIR, "vectorstore")
            
            # 벡터스토어가 없으면 기본 데이터로 생성
            if not os.path.exists(vectorstore_path):
                logger.info("Creating new vectorstore with default data...")
                cls._create_default_vectorstore(vectorstore_path)
            else:
                # 기존 벡터스토어 로드
                cls._vectorstore = FAISS.load_local(
                    vectorstore_path, 
                    cls._embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Loaded vectorstore with {cls._vectorstore.index.ntotal} vectors")
                
        except Exception as e:
            logger.error(f"Vectorstore initialization failed: {str(e)}")
            cls._vectorstore = None
    
    @classmethod
    def _create_default_vectorstore(cls, path: str):
        """기본 헬스/운동 지식으로 벡터스토어 생성"""
        try:
            # 기본 운동 지식
            default_docs = [
                # 운동 관련
                "스쿼트는 하체 운동의 기본으로, 대퇴사두근, 햄스트링, 둔근을 강화합니다. 올바른 자세: 발을 어깨너비로 벌리고, 무릎이 발끝을 넘지 않도록 주의하며 엉덩이를 뒤로 빼면서 앉습니다.",
                "푸시업은 가슴, 어깨, 삼두근을 강화하는 상체 운동입니다. 초보자는 무릎을 대고 시작하며, 점진적으로 표준 푸시업으로 발전시킵니다.",
                "플랭크는 코어 강화에 효과적입니다. 팔꿈치를 90도로 굽히고 전완을 바닥에 대고, 몸을 일직선으로 유지합니다. 30초부터 시작해 점진적으로 시간을 늘립니다.",
                
                # 영양 관련
                "단백질은 근육 성장과 회복에 필수적입니다. 체중 1kg당 0.8-2g의 단백질 섭취를 권장합니다. 운동 후 30분 이내 섭취가 효과적입니다.",
                "탄수화물은 운동 에너지원입니다. 운동 전 1-2시간 전에 복합 탄수화물을 섭취하면 지속적인 에너지를 얻을 수 있습니다.",
                "수분 섭취는 운동 성능에 중요합니다. 운동 전 500ml, 운동 중 15-20분마다 150-250ml, 운동 후 체중 감소량의 150%를 섭취합니다.",
                
                # 건강 관련
                "규칙적인 운동은 심혈관 건강을 개선하고, 당뇨병 위험을 감소시키며, 정신 건강에도 도움이 됩니다. 주 150분 이상의 중강도 운동을 권장합니다.",
                "충분한 수면은 근육 회복과 성장에 필수적입니다. 성인은 7-9시간의 수면이 필요하며, 운동 후 회복을 위해 특히 중요합니다.",
                "스트레칭은 유연성을 향상시키고 부상을 예방합니다. 운동 전 동적 스트레칭, 운동 후 정적 스트레칭을 권장합니다.",
            ]
            
            # 메타데이터 추가
            documents = []
            for i, doc in enumerate(default_docs):
                category = 'exercise' if i < 3 else 'nutrition' if i < 6 else 'health'
                documents.append({
                    'page_content': doc,
                    'metadata': {
                        'source': 'default',
                        'category': category,
                        'id': i
                    }
                })
            
            # FAISS 벡터스토어 생성
            texts = [doc['page_content'] for doc in documents]
            metadatas = [doc['metadata'] for doc in documents]
            
            cls._vectorstore = FAISS.from_texts(
                texts=texts,
                embedding=cls._embeddings,
                metadatas=metadatas
            )
            
            # 저장
            os.makedirs(path, exist_ok=True)
            cls._vectorstore.save_local(path)
            logger.info(f"Created default vectorstore with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to create default vectorstore: {str(e)}")
            cls._vectorstore = None
    
    def get_response(self, user_id: str, username: str, question: str, session_data: Dict = None) -> Dict:
        """사용자 질문에 대한 응답 생성"""
        start_time = time.time()
        
        try:
            # 1. 간단한 인사 처리
            simple_response = self._check_simple_questions(question)
            if simple_response:
                return {
                    'success': True,
                    'response': simple_response,
                    'response_time': time.time() - start_time,
                    'cached': True
                }
            
            # 2. 카테고리 분류
            category = self._classify_query(question)
            
            # 3. 벡터스토어에서 관련 지식 검색
            relevant_knowledge = []
            if VECTORSTORE_AVAILABLE and self._vectorstore and category:
                relevant_knowledge = self._search_knowledge(question, category)
            
            # 4. 시스템 프롬프트 생성
            system_prompt = self._create_system_prompt(username, session_data or {}, relevant_knowledge)
            
            # 5. 대화 컨텍스트 구성
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
            
            # 6. 모델 선택
            model = self._select_model_by_complexity(question, category)
            
            # 7. OpenAI API 호출
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            return {
                'success': True,
                'response': answer,
                'response_time': time.time() - start_time,
                'model_used': model,
                'category': category,
                'knowledge_used': len(relevant_knowledge)
            }
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return {
                'success': False,
                'response': "죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                'error': str(e),
                'response_time': time.time() - start_time
            }
    
    def _search_knowledge(self, query: str, category: str) -> List[Dict]:
        """벡터스토어에서 관련 지식 검색"""
        try:
            if not VECTORSTORE_AVAILABLE or not self._vectorstore:
                return []
            
            # 카테고리 기반 검색
            docs = self._vectorstore.similarity_search_with_score(query, k=3)
            
            relevant_docs = []
            for doc, score in docs:
                # 점수가 낮을수록 유사도가 높음
                if score < 0.8:  # 임계값
                    doc_category = doc.metadata.get('category', 'general')
                    # 같은 카테고리이거나 일반 지식인 경우
                    if doc_category == category or doc_category == 'general':
                        relevant_docs.append({
                            'content': doc.page_content,
                            'score': score,
                            'category': doc_category
                        })
            
            return relevant_docs[:2]  # 최대 2개만 사용
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {str(e)}")
            return []
    
    def _classify_query(self, query: str) -> Optional[str]:
        """쿼리를 카테고리로 분류"""
        query_lower = query.lower()
        
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def _check_simple_questions(self, question: str) -> Optional[str]:
        """간단한 질문에 대한 빠른 응답"""
        simple_patterns = {
            '안녕': "안녕하세요! 무엇을 도와드릴까요?",
            '고마워': "천만에요! 더 궁금한 점이 있으시면 언제든 물어보세요.",
            '감사': "도움이 되어 기쁩니다! 건강한 하루 보내세요.",
        }
        
        question_lower = question.lower()
        for pattern, response in simple_patterns.items():
            if pattern in question_lower:
                return response
        
        return None
    
    def _create_system_prompt(self, username: str, session_data: Dict, knowledge: List[Dict] = None) -> str:
        """시스템 프롬프트 생성"""
        prompt = f"""당신은 전문적이고 친근한 헬스케어 AI 어시스턴트입니다.
사용자의 건강 정보와 선호도를 고려하여 맞춤형 운동과 식단 조언을 제공합니다.
답변은 간결하고 실용적으로 하되, 핵심 정보는 놓치지 마세요.

사용자 정보:
- 이름: {username}
"""
        
        # 세션 데이터가 있으면 추가
        if session_data:
            if 'birth_date' in session_data:
                # birth_date로부터 나이 계산
                birth_date = session_data['birth_date']
                if isinstance(birth_date, str):
                    birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                age = (date.today() - birth_date).days // 365
                prompt += f"- 나이: {age}세\n"
            if 'gender' in session_data:
                prompt += f"- 성별: {session_data['gender']}\n"
            if 'height' in session_data:
                prompt += f"- 키: {session_data['height']}cm\n"
            if 'weight' in session_data:
                prompt += f"- 체중: {session_data['weight']}kg\n"
                # BMI 계산
                if 'height' in session_data and session_data['height'] > 0:
                    height_m = session_data['height'] / 100
                    bmi = session_data['weight'] / (height_m ** 2)
                    prompt += f"- BMI: {bmi:.1f}\n"
        
        # 관련 지식이 있으면 추가
        if knowledge:
            prompt += "\n참고 정보:\n"
            for k in knowledge:
                prompt += f"- {k['content'][:100]}...\n"
        
        prompt += "\n답변은 2-3 문단으로 간결하게 작성하세요."
        
        return prompt
    
    def _select_model_by_complexity(self, question: str, category: str = None) -> str:
        """질문 복잡도에 따라 모델 선택"""
        # 의학적 카테고리이거나 긴 질문이면 더 좋은 모델 사용
        if category == 'health' or len(question.split()) > 20:
            return "gpt-4o-mini"  # 더 저렴한 GPT-4 모델
        
        return "gpt-3.5-turbo"
    
    def get_health_consultation(self, user_data: Dict, question: str) -> Dict:
        """건강 상담 API"""
        return self.get_response(
            user_id=str(user_data.get('user_id', 'guest')),
            username=user_data.get('username', 'Guest'),
            question=question,
            session_data=user_data
        )
    
    def generate_workout_recommendation(self, user_data: Dict) -> Dict:
        """운동 추천 생성"""
        try:
            # birth_date로부터 나이 계산
            age = 30  # 기본값
            if 'birth_date' in user_data:
                birth_date = user_data['birth_date']
                if isinstance(birth_date, str):
                    birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                age = (date.today() - birth_date).days // 365
            
            prompt = f"""
            사용자 정보:
            - 나이: {age}세
            - 성별: {user_data.get('gender', '미지정')}
            - 체중: {user_data.get('weight', 70)}kg
            - 키: {user_data.get('height', 170)}cm
            - 운동 경험: {user_data.get('experience', '초급')}
            - 목표: {user_data.get('goal', '체중 감량')}
            
            위 정보를 바탕으로 오늘의 운동을 추천해주세요.
            JSON 형식으로 답변해주세요:
            {{
                "title": "운동 제목",
                "description": "운동 설명 (2-3문장)",
                "exercises": ["운동1", "운동2", "운동3"],
                "duration": "운동 시간",
                "intensity": "운동 강도"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 전문 피트니스 트레이너입니다. JSON 형식으로만 답변하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # JSON 파싱
            content = response.choices[0].message.content
            # JSON 블록 추출 (```json ... ``` 형식 처리)
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            return {
                'success': True,
                'recommendation': result
            }
            
        except Exception as e:
            logger.error(f"Workout recommendation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'recommendation': self._get_default_workout_recommendation()
            }
    
    def generate_nutrition_recommendation(self, user_data: Dict) -> Dict:
        """영양 추천 생성"""
        try:
            # birth_date로부터 나이 계산
            age = 30  # 기본값
            if 'birth_date' in user_data:
                birth_date = user_data['birth_date']
                if isinstance(birth_date, str):
                    birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                age = (date.today() - birth_date).days // 365
            
            prompt = f"""
            사용자 정보:
            - 나이: {age}세
            - 성별: {user_data.get('gender', '미지정')}
            - 체중: {user_data.get('weight', 70)}kg
            - 키: {user_data.get('height', 170)}cm
            - 목표: {user_data.get('goal', '균형 잡힌 식단')}
            - 알레르기: {', '.join(user_data.get('allergies', [])) or '없음'}
            
            위 정보를 바탕으로 오늘의 식단을 추천해주세요.
            JSON 형식으로 답변해주세요:
            {{
                "title": "식단 제목",
                "description": "식단 설명 (2-3문장)",
                "breakfast": ["음식1", "음식2"],
                "lunch": ["음식1", "음식2", "음식3"],
                "dinner": ["음식1", "음식2", "음식3"],
                "snack": ["간식1"],
                "total_calories": "예상 칼로리"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 전문 영양사입니다. JSON 형식으로만 답변하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # JSON 파싱
            content = response.choices[0].message.content
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            return {
                'success': True,
                'recommendation': result
            }
            
        except Exception as e:
            logger.error(f"Nutrition recommendation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'recommendation': self._get_default_nutrition_recommendation()
            }
    
    def _get_default_workout_recommendation(self) -> Dict:
        """기본 운동 추천"""
        return {
            "title": "기초 전신 운동",
            "description": "초보자를 위한 가벼운 전신 운동 루틴입니다.",
            "exercises": ["워밍업 5분", "푸시업 10회 x 3세트", "스쿼트 15회 x 3세트", "플랭크 30초 x 3세트"],
            "duration": "30분",
            "intensity": "중간"
        }
    
    def _get_default_nutrition_recommendation(self) -> Dict:
        """기본 영양 추천"""
        return {
            "title": "균형 잡힌 한식 식단",
            "description": "한국인에게 익숙한 균형 잡힌 식단입니다.",
            "breakfast": ["현미밥", "된장국", "계란말이", "김치"],
            "lunch": ["잡곡밥", "닭가슴살 구이", "샐러드", "나물 반찬"],
            "dinner": ["현미밥", "생선구이", "두부조림", "시금치나물"],
            "snack": ["사과 1개", "아몬드 10알"],
            "total_calories": "약 1800-2000kcal"
        }


# 전역 챗봇 인스턴스
_chatbot_instance = None

def get_chatbot() -> HealthAIChatbot:
    """챗봇 인스턴스 가져오기 (싱글톤)"""
    global _chatbot_instance
    if not _chatbot_instance:
        _chatbot_instance = HealthAIChatbot()
    return _chatbot_instance
