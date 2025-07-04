#!/bin/bash
# Railway 환경변수 대기 스크립트

echo "Waiting for Railway environment variables..."

# DATABASE_URL 대기
attempt=0
while [ -z "$DATABASE_URL" ] && [ $attempt -lt 20 ]; do
    echo "Waiting for DATABASE_URL... (attempt $((attempt+1))/20)"
    sleep 3
    # Railway가 환경변수를 주입할 때까지 대기
    source /etc/profile
    attempt=$((attempt+1))
done

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not found after 60 seconds"
    exit 1
fi

echo "DATABASE_URL found: ${DATABASE_URL:0:50}..."

# Redis URL 대기
attempt=0
while [ -z "$REDIS_URL" ] && [ $attempt -lt 10 ]; do
    echo "Waiting for REDIS_URL... (attempt $((attempt+1))/10)"
    sleep 2
    source /etc/profile
    attempt=$((attempt+1))
done

if [ -z "$REDIS_URL" ]; then
    echo "WARNING: REDIS_URL not found, continuing without Redis"
fi

# 마이그레이션 실행
echo "Running database migrations..."
python manage.py migrate --noinput

# Static 파일 수집
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 서버 시작 (WSGI 사용 - 더 안정적)
echo "Starting Django server with WSGI..."
exec gunicorn healthwise.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --keep-alive 2
