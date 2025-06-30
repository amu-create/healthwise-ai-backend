from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse

class CorsOptionsMiddleware(MiddlewareMixin):
    """
    Custom middleware to handle OPTIONS requests for CORS
    """
    def process_request(self, request):
        if request.method == 'OPTIONS':
            # Allow all OPTIONS requests
            response = HttpResponse()
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRFToken'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'  # 24 hours
            return response
        return None
