#!/bin/bash
# Railway 빠른 시작 스크립트 - 벡터스토어 초기화 스킵

echo "⚡ Fast startup - Skipping heavy operations..."

# DATABASE_URL 대기 (시간 단축)
attempt=0
while [ -z "$DATABASE_URL" ] && [ $attempt -lt 10 ]; do
    echo "Waiting for DATABASE_URL... ($((attempt+1))/10)"
    sleep 2  # 3초 → 2초로 단축
    source /etc/profile
    attempt=$((attempt+1))
done

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not found"
    exit 1
fi

echo "✅ DATABASE_URL found"

# Redis URL 대기 (시간 단축)  
attempt=0
while [ -z "$REDIS_URL" ] && [ $attempt -lt 5 ]; do
    echo "Waiting for REDIS_URL... ($((attempt+1))/5)"
    sleep 1  # 2초 → 1초로 단축
    source /etc/profile
    attempt=$((attempt+1))
done

# 🔥 벡터스토어 초기화 스킵
export SKIP_VECTORSTORE_INIT=true

# 마이그레이션 실행 (무거운 마이그레이션 스킵)
echo "Running essential migrations only..."
python manage.py migrate --noinput --fake-initial 2>/dev/null || python manage.py migrate --noinput

# Static 파일 수집 (압축 스킵)
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "🚀 Starting server with fast mode..."
exec gunicorn healthwise.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1 --timeout 120
