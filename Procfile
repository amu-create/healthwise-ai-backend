web: daphne -b 0.0.0.0 -p $PORT healthwise.asgi:application
release: python manage.py migrate --noinput || echo 'Migration skipped'
worker: celery -A healthwise worker --loglevel=info