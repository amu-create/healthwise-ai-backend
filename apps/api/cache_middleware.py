# backend/apps/api/cache_middleware.py
class NoCacheMiddleware:
    """HTML 파일에 대해 캐시를 비활성화하는 미들웨어"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # HTML 파일에 대해서만 캐시 비활성화
        content_type = response.get('Content-Type', '')
        if content_type.startswith('text/html') or request.path == '/' or request.path.endswith('.html'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['X-Content-Type-Options'] = 'nosniff'
            
            # 빌드 버전 정보 추가 (디버깅용)
            import os
            import time
            response['X-Build-Time'] = str(int(time.time()))
        
        return response
