import requests
from django.http import HttpResponse, JsonResponse
from django.views import View
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class ImageProxyView(View):
    def get(self, request):
        logger.info(f"Image proxy request: {request.GET}")
        url = request.GET.get('url')
        
        if not url:
            logger.error("No URL parameter provided")
            return JsonResponse({'error': 'URL parameter is required'}, status=400)
        
        # URL 검증 - tenor.com과 burnfit.io 허용
        parsed_url = urlparse(url)
        allowed_domains = ['media.tenor.com', 'media1.tenor.com', 'tenor.com', 'burnfit.io']
        
        if parsed_url.netloc not in allowed_domains:
            logger.error(f"Invalid domain: {parsed_url.netloc}")
            return JsonResponse({'error': 'Invalid domain'}, status=403)
        
        logger.info(f"Proxying image from: {url}")
        
        try:
            # 이미지 가져오기
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Content-Type 확인
            content_type = response.headers.get('Content-Type', 'image/gif')
            
            # 응답 생성
            http_response = HttpResponse(
                response.content,
                content_type=content_type
            )
            
            # CORS 헤더 추가
            http_response['Access-Control-Allow-Origin'] = '*'
            http_response['Cache-Control'] = 'public, max-age=86400'  # 24시간 캐시
            
            return http_response
            
        except requests.RequestException as e:
            return JsonResponse({'error': str(e)}, status=500)
