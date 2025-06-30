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


class OptimizedHealthChatbot:
    """최적화된 헬스케어 AI 챗봇 - 캐싱과 비동기 처리로 성능 개선"""
    
    # 클래스 변수로 공유 리소스 관리
    _embeddings = None
    _vectorstore = None
    _executor = ThreadPoolExecutor(max_workers=4)
    
    def __init__(self):
        logger.debug("🚀 OptimizedHealthChatbot 초기화 시작")
        try:
            api_key = settings.OPENAI_API_KEY
            self.client = OpenAI(api_key=api_key)
            self.max_recent_sessions = 7
            
            # Vectorstore 관련 설정
            self.vectorstore_path = os.path.join(settings.BASE_DIR, "api", "vectorstore")
            self.embedding_model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # 캐시 설정
            self.cache_timeout = 3600  # 1시간
            self.search_cache_timeout = 1800  # 30분
            
            # Vectorstore 초기화 (싱글톤 패턴)
            if not OptimizedHealthChatbot._embeddings:
                self._initialize_shared_resources()
            
            logger.debug("✅ OptimizedHealthChatbot 초기화 완료")
        except Exception as e:
            logger.error(f"❌ OptimizedHealthChatbot 초기화 실패: {str(e)}")
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
            vectorstore_path = os.path.join(settings.BASE_DIR, "api", "vectorstore")
            if os.path.exists(vectorstore_path):
                cls._vectorstore = FAISS.load_local(
                    vectorstore_path, 
                    cls._embeddings, 
                    allow_dangerous_deserialization=True
                )
                logger.info(f"✅ Vectorstore 로드 완료: {vectorstore_path}")
            else:
                logger.warning(f"⚠️ Vectorstore 경로가 존재하지 않음: {vectorstore_path}")
                
        except Exception as e:
            logger.error(f"❌ 공유 리소스 초기화 실패: {str(e)}")
    
    def _get_cache_key(self, prefix: str, query: str, user_id: int = None) -> str:
        """캐시 키 생성"""
        if user_id:
            key = f"{prefix}:{user_id}:{hashlib.md5(query.encode()).hexdigest()}"
        else:
            key = f"{prefix}:{hashlib.md5(query.encode()).hexdigest()}"
        return key
    
    def _search_pdf_knowledge_cached(self, query: str, k: int = 3) -> List[Dict]:
        """캐시된 PDF vectorstore 검색"""
        # 캐시 키 생성
        cache_key = self._get_cache_key("pdf_search", query)
        
        # 캐시 확인
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"✅ PDF 검색 캐시 히트: {cache_key}")
            return cached_result
        
        # 캐시 미스 - 실제 검색 수행
        result = self._search_pdf_knowledge(query, k)
        
        # 결과 캐싱
        cache.set(cache_key, result, self.search_cache_timeout)
        return result
    
    def _search_pdf_knowledge(self, query: str, k: int = 3) -> List[Dict]:
        """PDF vectorstore에서 관련 지식 검색"""
        if not OptimizedHealthChatbot._vectorstore:
            return []
            
        try:
            # 관련 문서 검색
            docs = OptimizedHealthChatbot._vectorstore.similarity_search_with_score(query, k=k)
            
            results = []
            for doc, score in docs:
                # 점수가 낮은 결과는 제외 (관련성이 낮음)
                if score > 0.8:  # 임계값 조정
                    continue
                    
                results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'source': doc.metadata.get('source', 'unknown'),
                    'score': score
                })
                
            logger.debug(f"✅ PDF 지식 검색 완료: {len(results)}개 문서 발견")
            return results
            
        except Exception as e:
            logger.error(f"❌ PDF 지식 검색 실패: {str(e)}")
            return []
    
    async def _search_pdf_knowledge_async(self, query: str, k: int = 3) -> List[Dict]:
        """비동기 PDF 검색"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            OptimizedHealthChatbot._executor,
            self._search_pdf_knowledge_cached,
            query,
            k
        )
    
    def get_response(self, user, question: str) -> Dict:
        """사용자 질문에 대한 응답 생성 (최적화된 버전)"""
        logger.debug("🎯 get_response 함수 시작")
        start_time = time.time()
        
        try:
            # 1. 간단한 인사나 일반적인 질문은 캐시에서 확인
            simple_response = self._check_simple_questions_cache(question)
            if simple_response:
                logger.debug(f"✅ 간단한 질문 캐시 히트: {time.time() - start_time:.2f}초")
                return simple_response
            
            # 2. 세션 가져오기 또는 생성
            session = self.get_or_create_session(user)
            
            # 3. 사용자 프로필 정보 가져오기 (캐시 사용)
            user_context = self._get_user_context_cached(user)
            
            # 4. 사용자 메시지 저장 (비동기)
            user_msg = ChatMessage.objects.create(
                user=user,
                session=session,
                sender='user',
                message=question,
                context={'action': 'question'}
            )
            
            # 5. 시스템 프롬프트 생성 (캐시 사용)
            system_prompt = self._get_cached_system_prompt(user, user_context)
            
            # 6. 필요한 경우에만 PDF 검색 수행
            pdf_knowledge = []
            if self._should_search_pdf(question):
                pdf_knowledge = self._search_pdf_knowledge_cached(question)
                logger.debug(f"📚 PDF 검색 완료: {len(pdf_knowledge)}개 문서")
            
            # 7. 대화 컨텍스트 구성 (최적화)
            messages = self._build_optimized_conversation_context(
                user, session, system_prompt, question, pdf_knowledge
            )
            
            # 8. OpenAI API 호출
            logger.debug(f"🤖 OpenAI API 호출 시작 (경과: {time.time() - start_time:.2f}초)")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            logger.debug(f"✅ OpenAI 응답 완료 (경과: {time.time() - start_time:.2f}초)")
            
            # 9. 봇 응답 저장 (비동기)
            ChatMessage.objects.create(
                user=user,
                session=session,
                sender='bot',
                message=answer,
                context={
                    'action': 'response',
                    'model': 'gpt-4o-mini',
                    'pdf_sources_used': len(pdf_knowledge),
                    'response_time': time.time() - start_time
                }
            )
            
            # 10. 백그라운드 작업 (선호도 추출 등)
            self._schedule_background_tasks(user, question, answer)
            
            logger.info(f"🎉 전체 응답 시간: {time.time() - start_time:.2f}초")
            
            return {
                'success': True,
                'response': answer,
                'raw_response': answer,
                'sources': len(pdf_knowledge),
                'user_context': user_context,
                'session_id': session.id,
                'response_time': time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {str(e)}")
            return {
                'success': False,
                'response': "죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                'error': str(e),
                'response_time': time.time() - start_time
            }
    
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
                    'cached': True
                }
        return None
    
    def _should_search_pdf(self, question: str) -> bool:
        """PDF 검색이 필요한지 판단"""
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
        
        # PDF 지식이 있으면 시스템 프롬프트에 추가
        if pdf_knowledge:
            knowledge_context = "\n\n참고 자료:\n"
            for idx, doc in enumerate(pdf_knowledge[:2]):  # 상위 2개만 사용
                knowledge_context += f"{idx+1}. {doc['content'][:300]}...\n"
            messages[0]["content"] += knowledge_context
        
        # 현재 세션의 최근 대화만 포함 (10개로 제한)
        recent_messages = session.messages.order_by('-created_at')[:10]
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
        OptimizedHealthChatbot._executor.submit(
            self._background_tasks, user, question, answer
        )
    
    def _background_tasks(self, user, question: str, answer: str):
        """백그라운드에서 실행될 작업들"""
        try:
            # 선호도 추출
            combined_text = f"사용자: {question}\n챗봇: {answer}"
            preferences = self._extract_preferences_from_text(combined_text)
            
            if any(preferences.values()):
                self._update_user_preferences(user, preferences)
            
            # 일일 추천 생성 (필요한 경우)
            self._generate_daily_recommendations(user)
            
        except Exception as e:
            logger.error(f"백그라운드 작업 실패: {str(e)}")
    
    # 기존 메서드들은 그대로 유지 (get_or_create_session, _get_user_context 등)
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
        prompt += "사용자의 건강 정보와 선호도를 고려하여 맞춤형 운동과 식단 조언을 제공합니다.\n\n"
        
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


# 전역 챗봇 인스턴스
chatbot_instance = None

def get_chatbot() -> OptimizedHealthChatbot:
    """챗봇 인스턴스 가져오기"""
    global chatbot_instance
    if not chatbot_instance:
        chatbot_instance = OptimizedHealthChatbot()
    return chatbot_instance
