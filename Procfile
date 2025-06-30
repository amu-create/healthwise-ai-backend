web: python manage.py migrate && python manage.py collectstatic --noinput && daphne -b 0.0.0.0 -p $PORT healthwise.asgi:application
worker: celery -A healthwise worker -l info
beat: celery -A healthwise beat -l info
