#!/bin/bash
# Railway 환경변수 대기 및 최적화된 시작 스크립트

echo "Starting Railway deployment script..."
echo "Python version: $(python --version)"
echo "Port: $PORT"

# 환경변수 확인
echo "Checking environment variables..."

# DATABASE_URL 확인 (Railway는 환경변수를 즉시 제공함)
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not found"
    echo "Available environment variables:"
    env | grep -E "(DATABASE|POSTGRES|DB)" | sed 's/=.*/=.../'
    exit 1
fi

echo "DATABASE_URL found: ${DATABASE_URL:0:50}..."

# Redis URL 확인
if [ -z "$REDIS_URL" ]; then
    echo "WARNING: REDIS_URL not found"
    echo "Redis-dependent features will be disabled"
else
    echo "REDIS_URL found: ${REDIS_URL:0:50}..."
fi

# Django 설정 검증
echo "Validating Django settings..."
python manage.py check --deploy

# 데이터베이스 연결 대기
echo "Waiting for database to be ready..."
python wait_for_db.py

# 마이그레이션 실행
echo "Running database migrations..."
python manage.py migrate --noinput

# Static 파일 수집
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# 캐시 테이블 생성 (필요한 경우)
echo "Creating cache tables..."
python manage.py createcachetable || true

# 슈퍼유저 생성 (개발/테스트용)
if [ "$DJANGO_CREATE_SUPERUSER" = "true" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput || true
fi

# 헬스체크 엔드포인트 테스트
echo "Testing health endpoint..."
python manage.py check

# 서버 시작 옵션 설정
if [ "$DJANGO_DEBUG" = "True" ]; then
    echo "Starting Django development server..."
    exec python manage.py runserver 0.0.0.0:$PORT
else
    echo "Starting Gunicorn production server..."
    # Gunicorn 최적화 설정
    exec gunicorn healthwise.wsgi:application \
        --bind 0.0.0.0:$PORT \
        --workers ${GUNICORN_WORKERS:-2} \
        --threads ${GUNICORN_THREADS:-4} \
        --worker-class sync \
        --worker-tmp-dir /dev/shm \
        --timeout ${GUNICORN_TIMEOUT:-120} \
        --keep-alive ${GUNICORN_KEEPALIVE:-5} \
        --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
        --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-100} \
        --access-logfile - \
        --error-logfile - \
        --log-level ${GUNICORN_LOG_LEVEL:-info} \
        --capture-output \
        --enable-stdio-inheritance
fi