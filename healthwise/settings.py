"""
Django settings for healthwise project.
Enhanced for session-based authentication with Netlify/Railway deployment.
"""

from pathlib import Path
import os
import time
import logging
from dotenv import load_dotenv
import dj_database_url

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Last updated: 2025-07-05 for deployment trigger
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Railway production
if not DEBUG:
    ALLOWED_HOSTS.extend(['healthwise-api-production.up.railway.app', '.railway.app', '*'])

# Application definition
INSTALLED_APPS = [
    'daphne',  # Daphne를 먼저 추가 (ASGI 서버)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'channels',  # Channels 추가
    'django_celery_beat',  # Celery Beat 추가
    'django_celery_results',  # Celery Results 추가
    'storages',  # 파일 스토리지 추가
    'api',  # Our API app
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS를 첫 번째로 이동
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'api.middleware.db_check.DatabaseConnectionMiddleware',  # DB 연결 체크 추가
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # CSRF 임시 비활성화
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'healthwise.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'healthwise.wsgi.application'
ASGI_APPLICATION = 'healthwise.asgi.application'  # ASGI 추가

# Database with retry logic for Railway
logger = logging.getLogger(__name__)

# Import Supabase configuration
try:
    from .settings_supabase import get_supabase_database_config, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY
    USE_SUPABASE = True
except ImportError:
    USE_SUPABASE = False

def get_database_config():
    """Get database configuration with better error handling"""
    # Check if we should use Supabase
    use_supabase = os.environ.get('USE_SUPABASE', 'True') == 'True'
    
    if use_supabase and USE_SUPABASE:
        logger.info("Using Supabase database")
        return get_supabase_database_config()
    
    # Fallback to Railway PostgreSQL
    database_url = os.environ.get('DATABASE_URL')
    
    # Railway에서 buildtime에 Reference Variable은 해석이 안 됨
    # 런타임에만 사용 가능
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        logger.info("Running in Railway environment")
        if database_url:
            logger.info(f"DATABASE_URL found: {database_url[:50]}...")
        else:
            logger.warning("DATABASE_URL not yet available (normal during build)")
    
    if database_url:
        return dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    else:
        # 빌드 타임이거나 로컬 개발시 임시 설정
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }

# Database configuration
DATABASES = {
    'default': get_database_config()
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = os.environ.get('STATIC_URL', '/static/')
STATIC_ROOT = os.environ.get('STATIC_ROOT', '/app/staticfiles')

# Media files
MEDIA_URL = os.environ.get('MEDIA_URL', '/media/')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', BASE_DIR / 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===== CORS 설정 =====
cors_origins_env = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'https://healthwiseaipro.netlify.app,http://localhost:3000,http://localhost:5173'
)

CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]

essential_origins = [
    'https://healthwiseaipro.netlify.app',
    'https://healthwise-ai.netlify.app',
    'http://localhost:3000',
    'http://localhost:5173',
]

for origin in essential_origins:
    if origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(origin)

# WebSocket을 위한 추가 설정
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^wss://healthwise-api-production\.up\.railway\.app$",
    r"^ws://localhost:8000$",
]

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-guest-id',
    'x-auth-user',
    'accept-language',
    'cookie',
]

# Static files configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # 기본 Django 인증
    'api.supabase_auth.SupabaseAuthBackend',  # Supabase 인증 추가
]

# Security settings for production
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
    
    # CSRF 설정 - 임시 비활성화로 세션 인증에 집중
    CSRF_TRUSTED_ORIGINS = [
        'https://healthwiseaipro.netlify.app',
        'https://healthwise-ai.netlify.app',
        'https://healthwise-api-production.up.railway.app',
    ]
    
    SECURE_SSL_REDIRECT = False
    
    # 세션 쿠키 설정 - 크로스 오리진 지원
    SESSION_COOKIE_SECURE = False  # HTTPS 강제하지 않음 (테스트용)
    SESSION_COOKIE_SAMESITE = None  # 크로스 오리진 허용
    SESSION_COOKIE_HTTPONLY = False  # JavaScript 접근 허용
    SESSION_COOKIE_DOMAIN = None  # 자동 도메인 설정
    
    # CSRF 쿠키 설정 - 임시로 완화
    CSRF_COOKIE_SECURE = False
    CSRF_COOKIE_SAMESITE = None  
    CSRF_COOKIE_HTTPONLY = False
    CSRF_COOKIE_DOMAIN = None
    
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
else:
    # 개발 환경에서는 세션 설정 단순화
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = None
    SESSION_COOKIE_HTTPONLY = False
    CSRF_COOKIE_SECURE = False
    CSRF_COOKIE_SAMESITE = None
    CSRF_COOKIE_HTTPONLY = False

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',  # 세션 인증 우선
        'api.jwt_auth.CustomJWTAuthentication',  # JWT 인증 보조
        'api.supabase_auth.SupabaseJWTAuthentication',  # Supabase JWT 인증 추가
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',  # 파일 업로드를 위해 추가
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'channels': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# Redis configuration with retry logic
def get_redis_config():
    """Get Redis configuration with better error handling"""
    redis_url = os.environ.get('REDIS_URL')
    
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        if redis_url:
            logger.info(f"REDIS_URL found: {redis_url[:50]}...")
        else:
            logger.warning("REDIS_URL not yet available (normal during build)")
    
    return redis_url

# Redis configuration
redis_url = get_redis_config()
if redis_url:
    import urllib.parse
    redis_parsed = urllib.parse.urlparse(redis_url)
    
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': redis_url,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
    
    # Channels configuration
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [redis_url],
            },
        },
    }
    
    # Celery configuration
    CELERY_BROKER_URL = redis_url
    CELERY_RESULT_BACKEND = redis_url
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = TIME_ZONE
    CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# 파일 업로드 설정
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# S3 설정 (옵션 - 환경변수로 제어)
if os.environ.get('USE_S3', 'False') == 'True':
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

# LangChain 설정
LANGCHAIN_VERBOSE = DEBUG
LANGCHAIN_CACHE = 'default' if redis_url else None

# API Keys (환경변수에서 가져오기)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
KAKAO_API_KEY = os.environ.get('KAKAO_API_KEY')

# 세션 설정 강화
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400 * 30  # 30일
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_NAME = 'healthwise_sessionid'  # 커스텀 세션 쿠키 이름

# CSRF 완전 비활성화 (개발/테스트 목적)
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
