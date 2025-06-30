from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils import translation
from ..serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer, ProfileUpdateSerializer,
    HealthOptionsSerializer
)
from apps.core.models import UserProfile, DISEASE_CHOICES, ALLERGY_CHOICES, ChatMessage, ChatSession
# from ..chatbot import get_chatbot
# from ..simple_chatbot import get_chatbot
# from ..enhanced_chatbot import get_chatbot
# from ..optimized_chatbot import get_chatbot
try:
    from ..ultrafast_chatbot_enhanced import get_chatbot  # 초고속 최적화 챗봇 사용 (다국어 지원)
except ImportError:
    try:
        from ..ultrafast_chatbot import get_chatbot  # 기본 ultrafast 챗봇
    except ImportError:
        try:
            from ..optimized_chatbot import get_chatbot  # 최적화 챗봇
        except ImportError:
            from ..simple_chatbot import get_chatbot  # Fallback to simple chatbot
from ..authentication import CsrfExemptSessionAuthentication
import logging
import traceback

logger = logging.getLogger(__name__)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """회원가입 뷰"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required for registration
    
    def create(self, request, *args, **kwargs):
        logger.info(f"Registration attempt with data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Registration validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = serializer.save()
            logger.info(f"User created successfully: {user.email}")
            
            # 자동 로그인
            login(request, user)
            
            # 사용자 정보 반환
            user_serializer = UserSerializer(user, context={'request': request})
            
            return Response({
                'user': user_serializer.data,
                'message': '회원가입이 완료되었습니다.'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response({
                'error': f'회원가입 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginView(APIView):
    """로그인 뷰"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # 사용자 인증
        user = authenticate(request, username=email, password=password)
        
        if user:
            login(request, user)
            
            # 명시적으로 세션 저장
            request.session.save()
            
            user_serializer = UserSerializer(user, context={'request': request})
            
            # 세션 ID 포함
            response_data = {
                'user': user_serializer.data,
                'message': '로그인되었습니다.',
                'session_id': request.session.session_key,
                'is_authenticated': True
            }
            
            # 로그 추가
            logger.info(f"Login successful for user: {user.email}, session_id: {request.session.session_key}")
            
            response = Response(response_data)
            
            # 명시적으로 세션 쿠키 설정 (개발 환경용)
            if request.session.session_key:
                response.set_cookie(
                    key='sessionid',
                    value=request.session.session_key,
                    max_age=None,
                    expires=None,
                    path='/',
                    domain=None,
                    secure=False,
                    httponly=True,
                    samesite='Lax'
                )
            
            return response
        else:
            return Response({
                'error': '이메일 또는 비밀번호가 올바르지 않습니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    """로그아웃 뷰"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        logout(request)
        return Response({'message': '로그아웃되었습니다.'})

class UserProfileView(APIView):
    """현재 사용자 정보 조회/수정"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    def patch(self, request):
        profile = request.user.profile
        serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            user_serializer = UserSerializer(request.user, context={'request': request})
            return Response({
                'user': user_serializer.data,
                'message': '프로필이 업데이트되었습니다.'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    """비밀번호 변경"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            
            # 현재 비밀번호 확인
            if not user.check_password(old_password):
                return Response({
                    'error': '현재 비밀번호가 올바르지 않습니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 새 비밀번호 설정
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # 비밀번호 변경 후 재로그인 필요
            logout(request)
            
            return Response({
                'message': '비밀번호가 변경되었습니다. 다시 로그인해주세요.'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_options(request):
    """건강 정보 옵션 목록"""
    # 언어 가져오기
    lang = request.GET.get('lang', 'ko')
    
    # 언어별 옵션 정의
    disease_options = {
        'ko': DISEASE_CHOICES,
        'en': [
            'Hypertension', 'Diabetes', 'Heart Disease', 'Arthritis', 'Asthma',
            'Thyroid Disease', 'Kidney Disease', 'Liver Disease', 'Gastrointestinal Disease', 'Anemia',
            'Osteoporosis', 'Depression', 'Anxiety Disorder', 'Sleep Disorder', 'Obesity',
            'Hyperlipidemia', 'Gout', 'Allergic Rhinitis', 'Atopy', 'Psoriasis'
        ],
        'es': [
            'Hipertensión', 'Diabetes', 'Enfermedad Cardíaca', 'Artritis', 'Asma',
            'Enfermedad de Tiroides', 'Enfermedad Renal', 'Enfermedad Hepática', 'Enfermedad Gastrointestinal', 'Anemia',
            'Osteoporosis', 'Depresión', 'Trastorno de Ansiedad', 'Trastorno del Sueño', 'Obesidad',
            'Hiperlipidemia', 'Gota', 'Rinitis Alérgica', 'Atopia', 'Psoriasis'
        ]
    }
    
    allergy_options = {
        'ko': ALLERGY_CHOICES,
        'en': [
            'Eggs', 'Milk', 'Wheat', 'Soy', 'Peanuts',
            'Tree Nuts', 'Fish', 'Shellfish', 'Crustaceans', 'Pork',
            'Beef', 'Chicken', 'Tomatoes', 'Strawberries', 'Peaches',
            'Kiwi', 'Bananas', 'Avocado', 'Buckwheat', 'Sesame'
        ],
        'es': [
            'Huevos', 'Leche', 'Trigo', 'Soja', 'Cacahuetes',
            'Frutos Secos', 'Pescado', 'Mariscos', 'Crustáceos', 'Cerdo',
            'Carne de Res', 'Pollo', 'Tomates', 'Fresas', 'Melocotones',
            'Kiwi', 'Plátanos', 'Aguacate', 'Trigo Sarraceno', 'Sésamo'
        ]
    }
    
    # 지원하지 않는 언어는 영어로 기본 설정
    if lang not in disease_options:
        lang = 'en'
    
    data = {
        'diseases': disease_options[lang],
        'allergies': allergy_options[lang]
    }
    serializer = HealthOptionsSerializer(data)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_email(request):
    """이메일 중복 확인"""
    email = request.query_params.get('email', '')
    
    if not email:
        return Response({
            'error': '이메일을 입력해주세요.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    exists = User.objects.filter(email=email).exists()
    
    return Response({
        'exists': exists,
        'message': '이미 사용 중인 이메일입니다.' if exists else '사용 가능한 이메일입니다.'
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """CSRF 토큰 제공"""
    return Response({
        'csrfToken': get_token(request)
    })

@method_decorator(csrf_exempt, name='dispatch')
class ChatbotView(APIView):
    """AI 챗봇 API"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]
    
    def post(self, request):
        """챗봇에게 메시지 전송"""
        logger.info("🌟"*20)
        logger.info("🎯 ChatbotView.post() 시작")
        logger.info(f"👤 요청 사용자: {request.user.email}")
        logger.info(f"🔐 인증 상태: {request.user.is_authenticated}")
        logger.info(f"📦 요청 데이터: {request.data}")
        logger.info(f"🌐 요청 헤더: {dict(request.headers)}")
        
        # 언어 설정
        user_language = request.data.get('language', 'ko')
        translation.activate(user_language)
        
        message = request.data.get('message', '').strip()
        logger.info(f"💬 추출된 메시지: '{message}'")
        logger.info(f"📏 메시지 길이: {len(message)}자")
        logger.info(f"🌍 요청 언어: {user_language}")
        
        if not message:
            logger.warning("⚠️ 빈 메시지 요청")
            return Response({
                'error': _('Please enter a message.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            logger.info("🔧 챗봇 처리 시작")
            
            # 챗봇 인스턴스 가져오기
            logger.info("  1️⃣ 챗봇 인스턴스 가져오기")
            chatbot = get_chatbot()
            logger.info(f"  ✅ 챗봇 인스턴스 타입: {type(chatbot).__name__}")
            
            # 응답 생성 (언어 정보 전달)
            logger.info("  2️⃣ 챗봇 응답 생성 시작")
            result = chatbot.get_response(request.user, message, language=user_language)
            logger.info(f"  ✅ 챗봇 응답 완료")
            logger.info(f"  📊 응답 성공 여부: {result.get('success')}")
            logger.info(f"  📦 응답 키: {list(result.keys())}")
            
            if result['success']:
                logger.info("  3️⃣ 성공 응답 준비")
                response_data = {
                    'response': result['response'],
                    'raw_response': result.get('raw_response'),
                    'sources': result.get('sources', 0),
                    'user_context': result.get('user_context')
                }
                logger.info(f"  ✅ 응답 데이터 준비 완료")
                logger.info(f"  📏 응답 길이: {len(result['response'])}자")
                logger.info("🎉 ChatbotView.post() 성공 완료")
                logger.info("🌟"*20)
                return Response(response_data)
            else:
                logger.error("  ❌ 챗봇 응답 실패")
                logger.error(f"  ❌ 오류 내용: {result.get('error')}")
                logger.error(f"  ❌ 오류 타입: {result.get('error_type')}")
                logger.error(f"  ❌ 트레이스백: {result.get('traceback', 'N/A')}")
                return Response({
                    'error': result['response'],
                    'debug_error': result.get('error'),
                    'debug_type': result.get('error_type'),
                    'debug_trace': result.get('traceback', 'N/A')[:500]  # 처음 500자만
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error("💥"*20)
            logger.error("💥 ChatbotView.post() 예외 발생!")
            logger.error(f"❌ 예외 타입: {type(e).__name__}")
            logger.error(f"❌ 예외 메시지: {str(e)}")
            logger.error(f"❌ 스택 트레이스:")
            logger.error(traceback.format_exc())
            logger.error("💥"*20)
            
            return Response({
                'error': _('An error occurred while generating the chatbot response.'),
                'debug_error': str(e),
                'debug_type': type(e).__name__,
                'debug_trace': traceback.format_exc()[:500]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """대화 기록 조회"""
        limit = int(request.query_params.get('limit', 50))
        
        try:
            chatbot = get_chatbot()
            history = chatbot.get_conversation_history(request.user, limit)
            
            return Response({
                'history': history,
                'total': len(history)
            })
            
        except Exception as e:
            logger.error(f"대화 기록 조회 오류: {str(e)}")
            return Response({
                'error': '대화 기록을 불러올 수 없습니다.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_chat_history(request):
    """대화 기록 삭제"""
    try:
        # 데이터베이스에서 삭제
        ChatMessage.objects.filter(user=request.user).delete()
        
        # 캐시 삭제
        chatbot = get_chatbot()
        chatbot.clear_user_cache(request.user.id)
        
        return Response({
            'message': '대화 기록이 삭제되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"대화 기록 삭제 오류: {str(e)}")
        return Response({
            'error': '대화 기록 삭제 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chatbot_status(request):
    """챗봇 상태 확인"""
    try:
        chatbot = get_chatbot()
        
        # 사용자 프로필 정보
        user_context = None
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            user_context = {
                'age': profile.age,
                'height': profile.height,
                'weight': profile.weight,
                'gender': profile.gender,  # display 메서드 제거 - 실제 값 전송
                'exercise_experience': profile.exercise_experience,  # display 메서드 제거 - 실제 값 전송
                'diseases': profile.diseases or [],
                'allergies': profile.allergies or []
            }
        
        # 대화 기록 수
        message_count = ChatMessage.objects.filter(user=request.user).count()
        
        return Response({
            'status': 'active',
            'user_context': user_context,
            'message_count': message_count,
            'has_profile': user_context is not None
        })
        
    except Exception as e:
        logger.error(f"챗봇 상태 확인 오류: {str(e)}")
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_recommendations(request):
    """일일 추천 조회"""
    try:
        # 언어 설정 가져오기
        language = request.GET.get('language', 'ko')
        
        chatbot = get_chatbot()
        recommendations = chatbot.get_daily_recommendations(request.user, language)
        
        return Response({
            'recommendations': recommendations,
            'date': timezone.now().date().isoformat()
        })
        
    except Exception as e:
        logger.error(f"일일 추천 조회 오류: {str(e)}")
        return Response({
            'error': '추천을 불러올 수 없습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ChatSessionView import
from ..views_sessions import ChatSessionView, get_session_messages, get_active_session
