import os
import logging
import re
import asyncio
import time
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.core.cache import cache
from apps.core.models import (
    ChatMessage, ChatSession, UserProfile, VectorizedChatHistory,
    DailyRecommendation, EXERCISE_CHOICES, FOOD_CATEGORIES
)
from openai import OpenAI
import traceback
import json
import numpy as np
from datetime import datetime, timedelta
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import torch
from concurrent.futures import ThreadPoolExecutor
import hashlib

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class UltraFastHealthChatbot:
    """초고속 헬스케어 AI 챗봇 - 강화된 사용자 기억 기능"""
    
    # 클래스 변수로 공유 리소스 관리
    _embeddings = None
    _vectorstore = None
    _executor = ThreadPoolExecutor(max_workers=4)
    
    def __init__(self):
        logger.debug("🚀 UltraFastHealthChatbot 초기화 시작")
        try:
            api_key = settings.OPENAI_API_KEY
            self.client = OpenAI(api_key=api_key)
            self.max_recent_sessions = 7
            
            # Vectorstore 관련 설정
            self.vectorstore_path = os.path.join(settings.BASE_DIR, "api", "vectorstore_optimized")
            # 최적화된 벡터스토어가 없으면 기존 것 사용
            if not os.path.exists(self.vectorstore_path):
                self.vectorstore_path = os.path.join(settings.BASE_DIR, "api", "vectorstore")
                logger.warning("⚠️ 최적화된 벡터스토어가 없습니다. 기존 벡터스토어 사용")
            
            self.embedding_model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # 캐시 설정
            self.cache_timeout = 3600  # 1시간
            self.search_cache_timeout = 1800  # 30분
            
            # 카테고리 키워드 정의 (사전 필터링용)
            self.category_keywords = {
                'exercise': ['운동', '스쿼트', '푸시업', '플랭크', '런닝', '요가', '필라테스', '근육', '체력', '트레이닝'],
                'nutrition': ['영양', '단백질', '탄수화물', '지방', '비타민', '칼로리', '식단', '음식', '다이어트', '식품'],
                'health': ['건강', '질병', '증상', '치료', '예방', '면역', '스트레스', '수면', '정신건강', '의학']
            }
            
            # 사용자 기억 패턴 정의
            self.memory_patterns = {
                'food_like': [
                    r'(.*?)(을|를)?\s*(좋아|선호|즐겨|자주 먹|많이 먹)',
                    r'(.*?)(이|가)?\s*(좋|맛있|최고)',
                    r'(.*?)\s*먹고\s*싶',
                ],
                'food_dislike': [
                    r'(.*?)(을|를)?\s*(싫어|못 먹|안 먹|별로)',
                    r'(.*?)(이|가)?\s*(싫|맛없|별로|안 좋)',
                    r'(.*?)\s*알레르기',
                ],
                'exercise_like': [
                    r'(.*?)\s*운동(을|를)?\s*(좋아|선호|즐겨|자주)',
                    r'(.*?)(을|를)?\s*하는\s*것(을|를)?\s*좋아',
                ],
                'exercise_dislike': [
                    r'(.*?)\s*운동(을|를)?\s*(싫어|못|안|별로)',
                    r'(.*?)(은|는)?\s*힘들|어려워',
                ],
                'health_condition': [
                    r'(.*?)(이|가)?\s*있어',
                    r'(.*?)\s*진단받',
                    r'(.*?)\s*앓고',
                ],
                'taste_preference': {
                    'spicy': ['매운', '맵', '스파이시', '칼칼'],
                    'sweet': ['단', '달', '스위트', '디저트'],
                    'salty': ['짠', '짭짤', '소금'],
                    'sour': ['신', '새콤', '시큼'],
                    'bitter': ['쓴', '씁쓸'],
                }
            }
            
            # Vectorstore 초기화 (싱글톤 패턴)
            if not UltraFastHealthChatbot._embeddings:
                self._initialize_shared_resources()
            
            logger.debug("✅ UltraFastHealthChatbot 초기화 완료")
        except Exception as e:
            logger.error(f"❌ UltraFastHealthChatbot 초기화 실패: {str(e)}")
            raise
    
    @classmethod
    def _initialize_shared_resources(cls):
        """공유 리소스 초기화 (한 번만 실행)"""
        try:
            logger.info("🔧 공유 리소스 초기화 시작")
            
            # 임베딩 모델 초기화
            cls._embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
                encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
            )
            logger.info("✅ 임베딩 모델 초기화 완료")
            
            # Vectorstore 로드
            vectorstore_path = os.path.join(settings.BASE_DIR, "api", "vectorstore_optimized")
            if not os.path.exists(vectorstore_path):
                vectorstore_path = os.path.join(settings.BASE_DIR, "api", "vectorstore")
                
            if os.path.exists(vectorstore_path):
                cls._vectorstore = FAISS.load_local(
                    vectorstore_path, 
                    cls._embeddings, 
                    allow_dangerous_deserialization=True
                )
                
                # IVF 인덱스인 경우 nprobe 설정
                if hasattr(cls._vectorstore.index, 'nprobe'):
                    cls._vectorstore.index.nprobe = 10  # 검색 시 탐색할 클러스터 수
                    logger.info(f"✅ IVF 인덱스 감지: nprobe={cls._vectorstore.index.nprobe}")
                
                logger.info(f"✅ Vectorstore 로드 완료: {vectorstore_path}")
                logger.info(f"   총 벡터 수: {cls._vectorstore.index.ntotal}")
            else:
                logger.warning(f"⚠️ Vectorstore 경로가 존재하지 않음: {vectorstore_path}")
                
        except Exception as e:
            logger.error(f"❌ 공유 리소스 초기화 실패: {str(e)}")
    
    def _classify_query(self, query: str) -> Optional[str]:
        """쿼리를 카테고리로 분류"""
        query_lower = query.lower()
        
        # 각 카테고리별 키워드 매칭 점수 계산
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                category_scores[category] = score
        
        # 가장 높은 점수의 카테고리 반환
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def _get_cache_key(self, prefix: str, query: str, user_id: int = None, category: str = None) -> str:
        """캐시 키 생성"""
        components = [prefix]
        if user_id:
            components.append(str(user_id))
        if category:
            components.append(category)
        components.append(hashlib.md5(query.encode()).hexdigest())
        
        return ":".join(components)
    
    def _search_pdf_knowledge_cached(self, query: str, k: int = 3, category: str = None) -> List[Dict]:
        """캐시된 PDF vectorstore 검색 (카테고리 필터링 포함)"""
        # 캐시 키 생성
        cache_key = self._get_cache_key("pdf_search", query, category=category)
        
        # 캐시 확인
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"✅ PDF 검색 캐시 히트: {cache_key}")
            return cached_result
        
        # 캐시 미스 - 실제 검색 수행
        result = self._search_pdf_knowledge(query, k, category)
        
        # 결과 캐싱
        cache.set(cache_key, result, self.search_cache_timeout)
        return result
    
    def _search_pdf_knowledge(self, query: str, k: int = 3, category: str = None) -> List[Dict]:
        """PDF vectorstore에서 관련 지식 검색 (메타데이터 필터링 적용)"""
        if not UltraFastHealthChatbot._vectorstore:
            return []
            
        try:
            start_time = time.time()
            
            # 카테고리가 있으면 더 많이 검색해서 필터링
            search_k = k * 3 if category else k
            
            # 관련 문서 검색
            docs = UltraFastHealthChatbot._vectorstore.similarity_search_with_score(query, k=search_k)
            
            results = []
            for doc, score in docs:
                # 점수가 낮은 결과는 제외 (관련성이 낮음)
                if score > 0.8:  # 임계값
                    continue
                
                # 카테고리 필터링
                if category and hasattr(doc, 'metadata'):
                    doc_category = doc.metadata.get('category', 'general')
                    if doc_category != category and doc_category != 'general':
                        continue
                
                results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata if hasattr(doc, 'metadata') else {},
                    'source': doc.metadata.get('source', 'unknown') if hasattr(doc, 'metadata') else 'unknown',
                    'score': score,
                    'category': doc.metadata.get('category', 'general') if hasattr(doc, 'metadata') else 'general'
                })
                
                # 필요한 개수만큼 찾으면 중단
                if len(results) >= k:
                    break
            
            elapsed = time.time() - start_time
            logger.debug(f"✅ PDF 지식 검색 완료: {len(results)}개 문서 ({elapsed:.3f}초)")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ PDF 지식 검색 실패: {str(e)}")
            return []
    
    async def _search_pdf_knowledge_async(self, query: str, k: int = 3, category: str = None) -> List[Dict]:
        """비동기 PDF 검색"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            UltraFastHealthChatbot._executor,
            self._search_pdf_knowledge_cached,
            query,
            k,
            category
        )
    
    def get_response(self, user, question: str, language: str = 'ko') -> Dict:
        """사용자 질문에 대한 응답 생성 (초고속 버전)"""
        logger.debug("🎯 get_response 함수 시작")
        logger.debug(f"🌍 언어 설정: {language}")
        start_time = time.time()
        
        try:
            # 1. 간단한 인사나 일반적인 질문은 캐시에서 확인
            simple_response = self._check_simple_questions_cache(question)
            if simple_response:
                logger.debug(f"✅ 간단한 질문 캐시 히트: {time.time() - start_time:.2f}초")
                return simple_response
            
            # 2. 쿼리 분류
            category = self._classify_query(question)
            logger.debug(f"📂 쿼리 카테고리: {category}")
            
            # 3. 세션 가져오기 또는 생성
            session = self.get_or_create_session(user)
            
            # 4. 사용자 프로필 정보 가져오기 (캐시 사용)
            user_context = self._get_user_context_cached(user)
            
            # 5. 사용자 기억 정보 가져오기
            user_memory = self._get_user_memory(user, question)
            
            # 6. 사용자 메시지 저장 (비동기) - 선호도 추출 포함
            user_msg = ChatMessage.objects.create(
                user=user,
                session=session,
                sender='user',
                message=question,
                context={'action': 'question', 'category': category}
            )
            
            # 7. 질문에서 선호도/기억 정보 추출 및 저장
            self._extract_and_save_preferences(user, question)
            
            # 8. 시스템 프롬프트 생성 (사용자 기억 포함)
            system_prompt = self._get_cached_system_prompt_with_memory(user, user_context, user_memory, language)
            
            # 9. 필요한 경우에만 PDF 검색 수행 (카테고리 필터링 적용)
            pdf_knowledge = []
            if self._should_search_pdf(question):
                pdf_knowledge = self._search_pdf_knowledge_cached(question, k=2, category=category)
                logger.debug(f"📚 PDF 검색 완료: {len(pdf_knowledge)}개 문서")
            
            # 10. 대화 컨텍스트 구성 (최적화)
            messages = self._build_optimized_conversation_context(
                user, session, system_prompt, question, pdf_knowledge
            )
            
            # 11. 모델 선택 (복잡도에 따라)
            model = self._select_model_by_complexity(question, category)
            logger.debug(f"🤖 선택된 모델: {model}")
            
            # 12. OpenAI API 호출
            logger.debug(f"🤖 OpenAI API 호출 시작 (경과: {time.time() - start_time:.2f}초)")
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=500  # 토큰 수 감소
            )
            
            answer = response.choices[0].message.content
            logger.debug(f"✅ OpenAI 응답 완료 (경과: {time.time() - start_time:.2f}초)")
            
            # 13. 봇 응답 저장 (비동기)
            ChatMessage.objects.create(
                user=user,
                session=session,
                sender='bot',
                message=answer,
                context={
                    'action': 'response',
                    'model': model,
                    'category': category,
                    'pdf_sources_used': len(pdf_knowledge),
                    'response_time': time.time() - start_time,
                    'user_memory_used': bool(user_memory)
                }
            )
            
            # 14. 백그라운드 작업 (응답에서도 선호도 추출)
            self._schedule_background_tasks(user, question, answer)
            
            logger.info(f"🎉 전체 응답 시간: {time.time() - start_time:.2f}초")
            
            return {
                'success': True,
                'response': answer,
                'raw_response': answer,
                'sources': len(pdf_knowledge),
                'user_context': user_context,
                'session_id': session.id,
                'response_time': time.time() - start_time,
                'model_used': model,
                'category': category,
                'memory_used': bool(user_memory)
            }
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {str(e)}")
            return {
                'success': False,
                'response': "죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                'error': str(e),
                'response_time': time.time() - start_time
            }
    
    def _get_user_memory(self, user, current_question: str) -> Dict:
        """사용자의 기억된 정보 가져오기"""
        memory = {
            'food_preferences': {},
            'exercise_preferences': {},
            'health_conditions': [],
            'important_facts': []
        }
        
        try:
            profile = user.profile
            
            # 프로필에서 기본 정보 가져오기
            if profile.preferred_foods:
                memory['food_preferences']['liked'] = profile.preferred_foods
            if profile.disliked_foods:
                memory['food_preferences']['disliked'] = profile.disliked_foods
            if profile.preferred_exercises:
                memory['exercise_preferences']['liked'] = profile.preferred_exercises
            if profile.disliked_exercises:
                memory['exercise_preferences']['disliked'] = profile.disliked_exercises
            if profile.diseases:
                memory['health_conditions'] = profile.diseases
            
            # 최근 대화에서 추출한 정보 확인
            recent_messages = ChatMessage.objects.filter(
                user=user,
                sender='user'
            ).order_by('-created_at')[:20]  # 최근 20개 메시지
            
            # 중요한 패턴 찾기
            for msg in recent_messages:
                text = msg.message.lower()
                
                # 맛 선호도
                for taste, keywords in self.memory_patterns['taste_preference'].items():
                    for keyword in keywords:
                        if keyword in text and ('싫' in text or '못' in text or '안' in text):
                            memory['important_facts'].append(f"{taste} 맛을 싫어함")
                        elif keyword in text and ('좋' in text or '자주' in text):
                            memory['important_facts'].append(f"{taste} 맛을 좋아함")
            
            # 현재 질문이 기억과 관련된 것인지 확인
            if '뭐' in current_question and '싫어' in current_question:
                # "뭐 싫어한다고?" 같은 질문 감지
                logger.debug(f"🧠 사용자 기억 요청 감지: {memory}")
            
            return memory
            
        except Exception as e:
            logger.error(f"사용자 기억 가져오기 실패: {str(e)}")
            return memory
    
    def _extract_and_save_preferences(self, user, text: str):
        """텍스트에서 선호도 추출하고 즉시 저장"""
        try:
            text_lower = text.lower()
            profile = user.profile
            updated = False
            
            # 음식 선호/비선호
            food_like_found = []
            food_dislike_found = []
            
            # "매운거 싫어해" 같은 패턴 처리
            if '매운' in text_lower and any(word in text_lower for word in ['싫어', '못 먹', '안 먹']):
                food_dislike_found.append('매운 음식')
            elif '매운' in text_lower and any(word in text_lower for word in ['좋아', '자주 먹']):
                food_like_found.append('매운 음식')
            
            # 단 음식
            if '단' in text_lower or '달' in text_lower:
                if any(word in text_lower for word in ['싫어', '못 먹', '안 먹']):
                    food_dislike_found.append('단 음식')
                elif any(word in text_lower for word in ['좋아', '자주 먹']):
                    food_like_found.append('단 음식')
            
            # 짠 음식
            if '짠' in text_lower or '짭짤' in text_lower:
                if any(word in text_lower for word in ['싫어', '못 먹', '안 먹']):
                    food_dislike_found.append('짠 음식')
                elif any(word in text_lower for word in ['좋아', '자주 먹']):
                    food_like_found.append('짠 음식')
            
            # 특정 음식들
            foods = ['치킨', '피자', '파스타', '김치', '된장', '커피', '차', '샐러드', '과일', '야채', '고기', '생선']
            for food in foods:
                if food in text_lower:
                    if any(word in text_lower for word in ['싫어', '못 먹', '안 먹', '별로']):
                        food_dislike_found.append(food)
                    elif any(word in text_lower for word in ['좋아', '자주 먹', '즐겨']):
                        food_like_found.append(food)
            
            # 운동 선호/비선호
            exercises = ['런닝', '달리기', '요가', '필라테스', '헬스', '웨이트', '수영', '자전거', '등산', '걷기']
            exercise_like_found = []
            exercise_dislike_found = []
            
            for exercise in exercises:
                if exercise in text_lower:
                    if any(word in text_lower for word in ['싫어', '못', '안', '힘들', '어려워']):
                        exercise_dislike_found.append(exercise)
                    elif any(word in text_lower for word in ['좋아', '자주', '즐겨']):
                        exercise_like_found.append(exercise)
            
            # 프로필 업데이트
            if food_like_found:
                current_likes = profile.preferred_foods or []
                for food in food_like_found:
                    if food not in current_likes:
                        current_likes.append(food)
                profile.preferred_foods = current_likes
                updated = True
                logger.info(f"✅ 음식 선호 추가: {food_like_found}")
            
            if food_dislike_found:
                current_dislikes = profile.disliked_foods or []
                for food in food_dislike_found:
                    if food not in current_dislikes:
                        current_dislikes.append(food)
                profile.disliked_foods = current_dislikes
                updated = True
                logger.info(f"✅ 음식 비선호 추가: {food_dislike_found}")
            
            if exercise_like_found:
                current_likes = profile.preferred_exercises or []
                for exercise in exercise_like_found:
                    if exercise not in current_likes:
                        current_likes.append(exercise)
                profile.preferred_exercises = current_likes
                updated = True
                logger.info(f"✅ 운동 선호 추가: {exercise_like_found}")
            
            if exercise_dislike_found:
                current_dislikes = profile.disliked_exercises or []
                for exercise in exercise_dislike_found:
                    if exercise not in current_dislikes:
                        current_dislikes.append(exercise)
                profile.disliked_exercises = current_dislikes
                updated = True
                logger.info(f"✅ 운동 비선호 추가: {exercise_dislike_found}")
            
            if updated:
                profile.save()
                # 캐시 무효화
                cache.delete(f"user_context:{user.id}")
                cache.delete(f"system_prompt:{user.id}:{timezone.now().date()}")
                
        except Exception as e:
            logger.error(f"선호도 추출 및 저장 실패: {str(e)}")
    
    def _get_cached_system_prompt_with_memory(self, user, user_context: Dict, user_memory: Dict, language: str = 'ko') -> str:
        """사용자 기억을 포함한 시스템 프롬프트 생성"""
        cache_key = f"system_prompt_memory:{user.id}:{timezone.now().date()}:{language}"
        cached_prompt = cache.get(cache_key)
        
        if cached_prompt:
            return cached_prompt
        
        prompt = self._create_system_prompt_with_memory(user, user_context, user_memory, language)
        cache.set(cache_key, prompt, 1800)  # 30분 캐시
        return prompt
    
    def _create_system_prompt_with_memory(self, user, user_context: Dict, user_memory: Dict, language: str = 'ko') -> str:
        """사용자 기억을 포함한 시스템 프롬프트 생성"""
        
        # 언어별 프롬프트
        if language == 'en':
            prompt = "You are a professional and friendly healthcare AI assistant.\n"
            prompt += "You provide personalized exercise and diet advice considering user's health information and preferences.\n"
            prompt += "Remember what the user said before and answer consistently.\n"
            prompt += "Keep your answers concise and practical, but don't miss key information.\n\n"
        else:  # 기본값 한국어
            prompt = "당신은 전문적이고 친근한 헬스케어 AI 어시스턴트입니다.\n"
            prompt += "사용자의 건강 정보와 선호도를 고려하여 맞춤형 운동과 식단 조언을 제공합니다.\n"
            prompt += "사용자가 이전에 말한 내용을 기억하고 일관성 있게 대답하세요.\n"
            prompt += "답변은 간결하고 실용적으로 하되, 핵심 정보는 놓치지 마세요.\n\n"
        
        # 언어별 사용자 정보 포맷
        if language == 'en':
            prompt += f"""
User Information:
- Name: {user_context.get('username', 'Unknown')}
- Age: {user_context.get('age', 'Unknown')} years old
- Gender: {user_context.get('gender', 'Unknown')}
- Height: {user_context.get('height', 'Unknown')}cm
- Weight: {user_context.get('weight', 'Unknown')}kg
- BMI: {user_context.get('bmi', 'Unknown')}
- Exercise Experience: {user_context.get('exercise_experience', 'Unknown')}
- Diseases: {', '.join(user_context.get('diseases', [])) or 'None'}
- Allergies: {', '.join(user_context.get('allergies', [])) or 'None'}

Important Preferences and Memories:
"""
        else:
            prompt += f"""
사용자 정보:
- 이름: {user_context.get('username', '알 수 없음')}
- 나이: {user_context.get('age', '알 수 없음')}세
- 성별: {user_context.get('gender', '알 수 없음')}
- 키: {user_context.get('height', '알 수 없음')}cm
- 체중: {user_context.get('weight', '알 수 없음')}kg
- BMI: {user_context.get('bmi', '알 수 없음')}
- 운동 경력: {user_context.get('exercise_experience', '알 수 없음')}
- 질병: {', '.join(user_context.get('diseases', [])) or '없음'}
- 알레르기: {', '.join(user_context.get('allergies', [])) or '없음'}

중요한 선호도와 기억:
"""
        
        # 언어별 선호도 표시
        if language == 'en':
            # 음식 선호도
            if user_memory.get('food_preferences'):
                if user_memory['food_preferences'].get('liked'):
                    prompt += f"- Liked foods: {', '.join(user_memory['food_preferences']['liked'])}\n"
                if user_memory['food_preferences'].get('disliked'):
                    prompt += f"- Disliked foods: {', '.join(user_memory['food_preferences']['disliked'])}\n"
            
            # 운동 선호도
            if user_memory.get('exercise_preferences'):
                if user_memory['exercise_preferences'].get('liked'):
                    prompt += f"- Liked exercises: {', '.join(user_memory['exercise_preferences']['liked'])}\n"
                if user_memory['exercise_preferences'].get('disliked'):
                    prompt += f"- Disliked exercises: {', '.join(user_memory['exercise_preferences']['disliked'])}\n"
            
            # 중요한 사실들
            if user_memory.get('important_facts'):
                prompt += f"- Other important information: {', '.join(user_memory['important_facts'])}\n"
            
            prompt += """
Consider all the information above when answering. Be sure to remember and mention the user's previously stated preferences or restrictions.
If the user asks something like "What did I say I don't like?", specifically tell them what's listed as disliked above.
Keep your answers concise, in 2-3 paragraphs.
Always respond in English.
"""
        else:
            # 음식 선호도
            if user_memory.get('food_preferences'):
                if user_memory['food_preferences'].get('liked'):
                    prompt += f"- 좋아하는 음식: {', '.join(user_memory['food_preferences']['liked'])}\n"
                if user_memory['food_preferences'].get('disliked'):
                    prompt += f"- 싫어하는 음식: {', '.join(user_memory['food_preferences']['disliked'])}\n"
            
            # 운동 선호도
            if user_memory.get('exercise_preferences'):
                if user_memory['exercise_preferences'].get('liked'):
                    prompt += f"- 좋아하는 운동: {', '.join(user_memory['exercise_preferences']['liked'])}\n"
                if user_memory['exercise_preferences'].get('disliked'):
                    prompt += f"- 싫어하는 운동: {', '.join(user_memory['exercise_preferences']['disliked'])}\n"
            
            # 중요한 사실들
            if user_memory.get('important_facts'):
                prompt += f"- 기타 중요 정보: {', '.join(user_memory['important_facts'])}\n"
            
            prompt += """
답변 시 위의 모든 정보를 고려하세요. 특히 사용자가 이전에 말한 선호도나 제한사항을 반드시 기억하고 언급하세요.
사용자가 "뭐 싫어한다고?" 같은 질문을 하면, 위에 기록된 싫어하는 것들을 구체적으로 알려주세요.
답변은 2-3 문단으로 간결하게 작성하세요.
한국어로 답변하세요.
"""
        
        return prompt
    
    def _select_model_by_complexity(self, question: str, category: str = None) -> str:
        """질문 복잡도에 따라 모델 선택"""
        # 의학적 용어나 복잡한 질문 패턴
        complex_patterns = [
            r'약물|부작용|질병|치료|진단|처방',
            r'어떻게.*왜|왜.*어떻게',
            r'비교.*분석|분석.*비교',
            r'장단점|효과.*차이'
        ]
        
        # 복잡한 질문인지 확인
        question_lower = question.lower()
        
        # 의학 카테고리이거나 복잡한 패턴이 있으면 gpt-4
        if category == 'health' or any(re.search(pattern, question_lower) for pattern in complex_patterns):
            return "gpt-4o-mini"
        
        # 긴 질문도 gpt-4
        if len(question.split()) > 20:
            return "gpt-4o-mini"
        
        # 그 외에는 gpt-3.5
        return "gpt-3.5-turbo"
    
    def _check_simple_questions_cache(self, question: str) -> Optional[Dict]:
        """간단한 질문에 대한 캐시 확인"""
        simple_patterns = [
            (r'안녕|하이|hello|hi', "안녕하세요! 무엇을 도와드릴까요?"),
            (r'감사|고마워|thanks?|thank you', "천만에요! 더 궁금한 점이 있으시면 언제든 물어보세요."),
            (r'잘가|바이|bye|goodbye', "안녕히 가세요! 건강하세요!"),
        ]
        
        question_lower = question.lower()
        for pattern, response in simple_patterns:
            if re.search(pattern, question_lower):
                return {
                    'success': True,
                    'response': response,
                    'raw_response': response,
                    'sources': 0,
                    'user_context': None,
                    'cached': True,
                    'response_time': 0.001
                }
        return None
    
    def _should_search_pdf(self, question: str) -> bool:
        """PDF 검색이 필요한지 판단"""
        # 카테고리가 있으면 검색
        if self._classify_query(question):
            return True
        
        # 특정 키워드가 포함된 경우에만 검색
        search_keywords = [
            '운동', '식단', '영양', '칼로리', '단백질', '탄수화물',
            '지방', '비타민', '미네랄', '다이어트', '벌크업', '근육',
            '유산소', '무산소', '스트레칭', '요가', '필라테스'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in search_keywords)
    
    def _get_user_context_cached(self, user) -> Dict:
        """캐시된 사용자 컨텍스트 가져오기"""
        cache_key = f"user_context:{user.id}"
        cached_context = cache.get(cache_key)
        
        if cached_context:
            return cached_context
        
        context = self._get_user_context(user)
        cache.set(cache_key, context, 300)  # 5분 캐시
        return context
    
    def _get_cached_system_prompt(self, user, user_context: Dict) -> str:
        """캐시된 시스템 프롬프트 가져오기"""
        cache_key = f"system_prompt:{user.id}:{timezone.now().date()}"
        cached_prompt = cache.get(cache_key)
        
        if cached_prompt:
            return cached_prompt
        
        prompt = self._create_system_prompt(user, user_context)
        cache.set(cache_key, prompt, 3600)  # 1시간 캐시
        return prompt
    
    def _build_optimized_conversation_context(self, user, session, system_prompt: str, 
                                            current_question: str, pdf_knowledge: List[Dict]) -> List[Dict]:
        """최적화된 대화 컨텍스트 구성"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # PDF 지식이 있으면 시스템 프롬프트에 추가 (최대 2개, 각 200자)
        if pdf_knowledge:
            knowledge_context = "\n\n참고 자료:\n"
            for idx, doc in enumerate(pdf_knowledge[:2]):
                knowledge_context += f"{idx+1}. {doc['content'][:200]}...\n"
            messages[0]["content"] += knowledge_context
        
        # 현재 세션의 최근 대화만 포함 (5개로 제한)
        recent_messages = session.messages.order_by('-created_at')[:5]
        for msg in reversed(list(recent_messages)[1:]):  # 현재 메시지 제외
            if msg.sender == 'user':
                messages.append({"role": "user", "content": msg.message})
            else:
                messages.append({"role": "assistant", "content": msg.message})
        
        # 현재 질문 추가
        messages.append({"role": "user", "content": current_question})
        
        return messages
    
    def _schedule_background_tasks(self, user, question: str, answer: str):
        """백그라운드 작업 스케줄링"""
        # ThreadPoolExecutor를 사용하여 비동기 실행
        UltraFastHealthChatbot._executor.submit(
            self._background_tasks, user, question, answer
        )
    
    def _background_tasks(self, user, question: str, answer: str):
        """백그라운드에서 실행될 작업들"""
        try:
            # 답변에서도 선호도 추출
            self._extract_and_save_preferences(user, answer)
            
            # 일일 추천 생성 (필요한 경우)
            self._generate_daily_recommendations(user)
            
            # 중요한 대화는 벡터화하여 저장 (3세션 이상 지나면)
            self._vectorize_important_conversations(user)
            
        except Exception as e:
            logger.error(f"백그라운드 작업 실패: {str(e)}")
    
    def _vectorize_important_conversations(self, user):
        """중요한 대화를 벡터화하여 저장"""
        try:
            # 마지막 벡터화 시점 확인
            last_vectorized = VectorizedChatHistory.objects.filter(
                user=user
            ).order_by('-created_at').first()
            
            # 3세션 이상 지났는지 확인
            session_count = ChatSession.objects.filter(
                user=user,
                started_at__gt=last_vectorized.created_at if last_vectorized else timezone.now() - timedelta(days=30)
            ).count()
            
            if session_count >= 3:
                # 중요한 대화 추출 및 벡터화
                important_messages = ChatMessage.objects.filter(
                    user=user,
                    created_at__gt=last_vectorized.created_at if last_vectorized else timezone.now() - timedelta(days=30)
                ).filter(
                    Q(message__icontains='좋아') | Q(message__icontains='싫어') |
                    Q(message__icontains='못 먹') | Q(message__icontains='알레르기') |
                    Q(message__icontains='질병') | Q(message__icontains='선호')
                )
                
                for msg in important_messages:
                    # 벡터화 및 저장
                    VectorizedChatHistory.objects.create(
                        user=user,
                        session=msg.session,
                        message=msg.message,
                        sender=msg.sender,
                        context={
                            'original_context': msg.context,
                            'vectorized_at': timezone.now().isoformat()
                        }
                    )
                
                logger.info(f"✅ {len(important_messages)}개의 중요 대화 벡터화 완료")
                
        except Exception as e:
            logger.error(f"대화 벡터화 실패: {str(e)}")
    
    # 기존 메서드들은 그대로 유지
    def get_or_create_session(self, user) -> ChatSession:
        """활성 세션 가져오기 또는 새 세션 생성"""
        # 활성 세션 확인
        active_session = ChatSession.objects.filter(
            user=user,
            is_active=True
        ).first()
        
        if active_session:
            # 마지막 활동이 1시간 이상 지났으면 새 세션 시작
            last_message = active_session.messages.order_by('-created_at').first()
            if last_message and (timezone.now() - last_message.created_at).seconds > 3600:
                active_session.end_session()
                active_session = None
        
        if not active_session:
            # 새 세션 생성
            active_session = ChatSession.objects.create(user=user)
            logger.debug(f"📝 새 세션 생성: {active_session.id}")
        
        return active_session
    
    def _get_user_context(self, user) -> Dict:
        """사용자 컨텍스트 정보 수집"""
        user_context = {'username': user.username}
        
        if hasattr(user, 'profile'):
            profile = user.profile
            
            # BMI 계산
            bmi = None
            if profile.height and profile.weight:
                height_m = profile.height / 100
                bmi = round(profile.weight / (height_m ** 2), 1)
            
            user_context.update({
                'age': profile.age,
                'height': profile.height,
                'weight': profile.weight,
                'bmi': bmi,
                'gender': profile.get_gender_display(),
                'exercise_experience': profile.get_exercise_experience_display(),
                'diseases': profile.diseases or [],
                'allergies': profile.allergies or [],
                'preferred_exercises': profile.preferred_exercises or [],
                'preferred_foods': profile.preferred_foods or [],
                'disliked_exercises': profile.disliked_exercises or [],
                'disliked_foods': profile.disliked_foods or []
            })
        
        return user_context
    
    def _create_system_prompt(self, user, user_context: Dict) -> str:
        """시스템 프롬프트 생성"""
        prompt = "당신은 전문적이고 친근한 헬스케어 AI 어시스턴트입니다.\n"
        prompt += "사용자의 건강 정보와 선호도를 고려하여 맞춤형 운동과 식단 조언을 제공합니다.\n"
        prompt += "답변은 간결하고 실용적으로 하되, 핵심 정보는 놓치지 마세요.\n\n"
        
        prompt += f"""
사용자 정보:
- 이름: {user_context.get('username', '알 수 없음')}
- 나이: {user_context.get('age', '알 수 없음')}세
- 성별: {user_context.get('gender', '알 수 없음')}
- 키: {user_context.get('height', '알 수 없음')}cm
- 체중: {user_context.get('weight', '알 수 없음')}kg
- BMI: {user_context.get('bmi', '알 수 없음')}
- 운동 경력: {user_context.get('exercise_experience', '알 수 없음')}
- 질병: {', '.join(user_context.get('diseases', [])) or '없음'}
- 알레르기: {', '.join(user_context.get('allergies', [])) or '없음'}

답변 시 사용자의 건강 상태, 선호도, 제한사항을 반드시 고려하세요.
답변은 2-3 문단으로 간결하게 작성하세요.
"""
        
        return prompt
    
    def _extract_preferences_from_text(self, text: str) -> Dict:
        """텍스트에서 선호도 정보 추출 (간단한 버전)"""
        preferences = {
            'liked_exercises': [],
            'disliked_exercises': [],
            'liked_foods': [],
            'disliked_foods': [],
            'other_preferences': {}
        }
        
        # 간단한 키워드 기반 추출만 수행
        text_lower = text.lower()
        
        # 매운 음식 키워드 검색
        if any(word in text_lower for word in ['매운', '매워', '맵게', '맵다']):
            if any(word in text_lower for word in ['싫어', '싫다', '못 먹', '안 먹']):
                preferences['other_preferences']['spicy_preference'] = 'dislike'
            elif any(word in text_lower for word in ['좋아', '좋다', '잘 먹']):
                preferences['other_preferences']['spicy_preference'] = 'like'
        
        return preferences
    
    def _update_user_preferences(self, user, preferences: Dict):
        """사용자 프로필에 선호도 업데이트"""
        try:
            profile = user.profile
            
            # 매운 음식 선호도 처리
            other_prefs = preferences.get('other_preferences', {})
            if other_prefs.get('spicy_preference') == 'dislike':
                disliked = profile.disliked_foods or []
                if '매운 음식' not in disliked:
                    disliked.append('매운 음식')
                    profile.disliked_foods = disliked
                    profile.save()
                    
                    # 캐시 무효화
                    cache.delete(f"user_context:{user.id}")
                    
        except Exception as e:
            logger.error(f"선호도 업데이트 실패: {str(e)}")
    
    def _generate_daily_recommendations(self, user):
        """일일 추천 생성 (간단한 체크만)"""
        today = timezone.now().date()
        
        # 오늘의 추천이 이미 있는지 확인
        existing = DailyRecommendation.objects.filter(
            user=user,
            date=today
        ).exists()
        
        if not existing:
            # 실제 생성은 별도 태스크로 처리
            logger.info(f"일일 추천 생성 필요: {user.username}")
    
    def get_conversation_history(self, user, limit: int = 50) -> List[Dict]:
        """대화 기록 가져오기"""
        # 캐시 확인
        cache_key = f"chat_history:{user.id}:{limit}"
        cached_history = cache.get(cache_key)
        if cached_history:
            return cached_history
        
        # 최근 세션들의 메시지
        recent_sessions = ChatSession.objects.filter(
            user=user
        ).order_by('-started_at')[:self.max_recent_sessions]
        
        messages = ChatMessage.objects.filter(
            session__in=recent_sessions
        ).order_by('-created_at')[:limit]
        
        history = []
        for msg in reversed(messages):
            history.append({
                'id': msg.id,
                'session_id': msg.session_id,
                'sender': msg.sender,
                'message': msg.message,
                'timestamp': msg.created_at.isoformat(),
                'context': msg.context
            })
        
        # 캐시에 저장
        cache.set(cache_key, history, 60)  # 1분 캐시
        return history
    
    def clear_user_cache(self, user_id: int):
        """사용자 캐시 삭제"""
        # 모든 관련 캐시 삭제
        cache_keys = [
            f"user_context:{user_id}",
            f"system_prompt:{user_id}:*",
            f"system_prompt_memory:{user_id}:*",
            f"chat_history:{user_id}:*"
        ]
        
        for key_pattern in cache_keys:
            if '*' in key_pattern:
                # 패턴 매칭은 Redis 등 고급 캐시 백엔드에서만 지원
                pass
            else:
                cache.delete(key_pattern)
        
        # 현재 활성 세션 종료
        ChatSession.objects.filter(
            user_id=user_id,
            is_active=True
        ).update(is_active=False, ended_at=timezone.now())
    
    def get_daily_recommendations(self, user, language: str = 'ko') -> Dict:
        """오늘의 추천 가져오기"""
        today = timezone.now().date()
        recommendations = DailyRecommendation.objects.filter(
            user=user,
            date=today
        )
        
        result = {
            'workout': None,
            'diet': None
        }
        
        for rec in recommendations:
            result[rec.type] = {
                'title': rec.title,
                'description': rec.description,
                'details': rec.details,
                'reasoning': rec.reasoning
            }
        
        # 추천이 없으면 생성 시도
        if not result['workout'] and not result['diet']:
            self._generate_daily_recommendations_full(user, language)
            # 다시 조회
            recommendations = DailyRecommendation.objects.filter(
                user=user,
                date=today
            )
            for rec in recommendations:
                result[rec.type] = {
                    'title': rec.title,
                    'description': rec.description,
                    'details': rec.details,
                    'reasoning': rec.reasoning
                }
        
        return result
    
    def _generate_daily_recommendations_full(self, user, language: str = 'ko'):
        """일일 추천 실제 생성"""
        today = timezone.now().date()
        
        # 오늘의 추천이 이미 있는지 확인
        existing_recommendations = DailyRecommendation.objects.filter(
            user=user,
            date=today
        )
        
        if existing_recommendations.exists():
            return
        
        try:
            profile = user.profile
            
            # BMI 계산
            bmi = None
            if profile.height and profile.weight:
                height_m = profile.height / 100
                bmi = round(profile.weight / (height_m ** 2), 1)
            
            # 운동 추천 생성
            workout_recommendation = self._generate_workout_recommendation(user, profile, bmi, language)
            if workout_recommendation:
                DailyRecommendation.objects.create(
                    user=user,
                    type='workout',
                    **workout_recommendation
                )
            
            # 식단 추천 생성
            diet_recommendation = self._generate_diet_recommendation(user, profile, bmi, language)
            if diet_recommendation:
                DailyRecommendation.objects.create(
                    user=user,
                    type='diet',
                    **diet_recommendation
                )
            
            logger.info(f"✅ {user.username}님의 일일 추천 생성 완료")
            
        except Exception as e:
            logger.error(f"일일 추천 생성 실패: {str(e)}")
    
    def _generate_workout_recommendation(self, user, profile, bmi, language: str = 'ko') -> Optional[Dict]:
        """운동 추천 생성"""
        try:
            # 추천 근거 수집
            reasoning_data = {
                'bmi': bmi,
                'experience': profile.get_exercise_experience_display(),
                'preferred_exercises': profile.preferred_exercises or [],
                'disliked_exercises': profile.disliked_exercises or [],
                'diseases': profile.diseases or [],
                'age': profile.age
            }
            
            # 언어별 프롬프트
            if language == 'en':
                prompt = f"""
                User information:
                - BMI: {bmi}
                - Exercise experience: {reasoning_data['experience']}
                - Preferred exercises: {', '.join(reasoning_data['preferred_exercises']) or 'None'}
                - Disliked exercises: {', '.join(reasoning_data['disliked_exercises']) or 'None'}
                - Diseases: {', '.join(reasoning_data['diseases']) or 'None'}
                - Age: {reasoning_data['age']} years old
                
                Based on the above information, please recommend today's exercise.
                Please answer in JSON format:
                {{
                    "title": "Exercise title",
                    "description": "Exercise description (2-3 sentences)",
                    "details": {{
                        "duration": "Exercise duration",
                        "intensity": "Exercise intensity",
                        "exercises": ["exercise1", "exercise2", "exercise3"]
                    }},
                    "reasoning": "Reason for recommendation (2-3 sentences)"
                }}
                All text must be in English.
                """
            else:  # 기본값 한국어
                prompt = f"""
                사용자 정보:
                - BMI: {bmi}
                - 운동 경력: {reasoning_data['experience']}
                - 선호 운동: {', '.join(reasoning_data['preferred_exercises']) or '없음'}
                - 싫어하는 운동: {', '.join(reasoning_data['disliked_exercises']) or '없음'}
                - 질병: {', '.join(reasoning_data['diseases']) or '없음'}
                - 나이: {reasoning_data['age']}세
                
                위 정보를 바탕으로 오늘의 운동을 추천해주세요.
                JSON 형식으로 답변해주세요:
                {{
                    "title": "운동 제목",
                    "description": "운동 설명 (2-3문장)",
                    "details": {{
                        "duration": "운동 시간",
                        "intensity": "운동 강도",
                        "exercises": ["운동1", "운동2", "운동3"]
                    }},
                    "reasoning": "추천 이유 (2-3문장)"
                }}
                """
            
            system_content = "당신은 전문 피트니스 트레이너입니다." if language == 'ko' else "You are a professional fitness trainer."
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # JSON 파싱
            result = json.loads(response.choices[0].message.content)
            result['based_on'] = reasoning_data
            
            return result
            
        except Exception as e:
            logger.error(f"운동 추천 생성 실패: {str(e)}")
            return None
    
    def _generate_diet_recommendation(self, user, profile, bmi, language: str = 'ko') -> Optional[Dict]:
        """식단 추천 생성"""
        try:
            # 추천 근거 수집
            reasoning_data = {
                'bmi': bmi,
                'preferred_foods': profile.preferred_foods or [],
                'disliked_foods': profile.disliked_foods or [],
                'allergies': profile.allergies or [],
                'diseases': profile.diseases or []
            }
            
            # 언어별 프롬프트
            if language == 'en':
                prompt = f"""
                User information:
                - BMI: {bmi}
                - Preferred foods: {', '.join(reasoning_data['preferred_foods']) or 'None'}
                - Disliked foods: {', '.join(reasoning_data['disliked_foods']) or 'None'}
                - Allergies: {', '.join(reasoning_data['allergies']) or 'None'}
                - Diseases: {', '.join(reasoning_data['diseases']) or 'None'}
                
                Based on the above information, please recommend today's diet.
                Please answer in JSON format:
                {{
                    "title": "Diet title",
                    "description": "Diet description (2-3 sentences)",
                    "details": {{
                        "breakfast": ["food1", "food2"],
                        "lunch": ["food1", "food2", "food3"],
                        "dinner": ["food1", "food2", "food3"],
                        "snack": ["snack1"]
                    }},
                    "reasoning": "Reason for recommendation (2-3 sentences)"
                }}
                All text must be in English.
                """
            else:  # 기본값 한국어
                prompt = f"""
                사용자 정보:
                - BMI: {bmi}
                - 선호 음식: {', '.join(reasoning_data['preferred_foods']) or '없음'}
                - 싫어하는 음식: {', '.join(reasoning_data['disliked_foods']) or '없음'}
                - 알레르기: {', '.join(reasoning_data['allergies']) or '없음'}
                - 질병: {', '.join(reasoning_data['diseases']) or '없음'}
                
                위 정보를 바탕으로 오늘의 식단을 추천해주세요.
                JSON 형식으로 답변해주세요:
                {{
                    "title": "식단 제목",
                    "description": "식단 설명 (2-3문장)",
                    "details": {{
                        "breakfast": ["음식1", "음식2"],
                        "lunch": ["음식1", "음식2", "음식3"],
                        "dinner": ["음식1", "음식2", "음식3"],
                        "snack": ["간식1"]
                    }},
                    "reasoning": "추천 이유 (2-3문장)"
                }}
                """
            
            system_content = "당신은 전문 영양사입니다." if language == 'ko' else "You are a professional nutritionist."
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # JSON 파싱
            result = json.loads(response.choices[0].message.content)
            result['based_on'] = reasoning_data
            
            return result
            
        except Exception as e:
            logger.error(f"식단 추천 생성 실패: {str(e)}")
            return None


# 전역 챗봇 인스턴스
chatbot_instance = None

def get_chatbot() -> UltraFastHealthChatbot:
    """챗봇 인스턴스 가져오기"""
    global chatbot_instance
    if not chatbot_instance:
        chatbot_instance = UltraFastHealthChatbot()
    return chatbot_instance
