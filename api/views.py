from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def test_api(request):
    return Response({
        'message': 'API is working!',
        'method': request.method,
    })

@api_view(['GET'])
def guest_profile(request):
    return Response({
        'id': 'guest-123',
        'username': 'guest',
        'email': 'guest@example.com',
    })

@api_view(['GET'])
def auth_csrf(request):
    return Response({
        'csrfToken': 'dummy-csrf-token',
    })