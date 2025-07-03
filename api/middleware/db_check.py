import time
import logging
from django.db import connection
from django.db.utils import OperationalError
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class DatabaseConnectionMiddleware:
    """
    Railway 환경에서 DATABASE_URL이 늦게 주입되는 경우를 대비한 미들웨어
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.db_checked = False

    def __call__(self, request):
        # Health check 엔드포인트는 DB 체크 건너뛰기
        if request.path == '/api/health/':
            return self.get_response(request)
        
        # DB 연결 체크 (첫 요청에서만)
        if not self.db_checked:
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # DB 연결 테스트
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                    self.db_checked = True
                    logger.info("Database connection successful")
                    break
                except OperationalError as e:
                    logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        return JsonResponse({
                            'error': 'Database connection failed',
                            'message': 'Service is starting up, please try again in a few seconds'
                        }, status=503)
        
        response = self.get_response(request)
        return response
