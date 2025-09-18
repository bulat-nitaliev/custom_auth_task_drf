import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from auth_task.models import User
from django.http import JsonResponse
from rest_framework import status

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пропускаем аутентификацию для эндпоинтов регистрации и входа
        if request.path in ['/api/users/register/', '/api/users/login/']:
            return self.get_response(request)
            
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse(
                {'error': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        if auth_header.startswith('Bearer '):
           
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user = User.objects.get(id=payload['id'], is_active=True)
                request.user = user
            except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
                return JsonResponse({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return JsonResponse(
                {'error': 'Invalid authorization header format'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        return self.get_response(request)