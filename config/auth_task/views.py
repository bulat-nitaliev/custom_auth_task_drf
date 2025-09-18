from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, AccessRule, BusinessElement
from .serializers import UserSerializer, UserRegisterSerializer
from .permissions import CustomPermission
from rest_framework.permissions import IsAuthenticated
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    business_element = 'users'

    @action(detail=False, methods=['post'], url_path='register', url_name='register')
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'token': user.generate_jwt()}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='login', url_name='login')
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return Response({'token': user.generate_jwt()})
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='logout', url_name='logout')
    def logout(self, request):
        return Response({'message': 'Logged out successfully'})

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class MockDataViewSet(viewsets.ViewSet):
    permission_classes = [CustomPermission]  # Добавляем проверку прав доступа
    business_element = 'mock_data'  # Указываем, к какому бизнес-элементу относятся эти данные
    
    def list(self, request):
        # Проверка прав доступа происходит автоматически через CustomPermission
        # Если доступ разрешен, возвращаем mock-данные
        return Response([
            {'id': 1, 'name': 'Test Object 1', 'owner': request.user.id},
            {'id': 2, 'name': 'Test Object 2', 'owner': request.user.id},
            {'id': 3, 'name': 'Test Object 3', 'owner': 999},  # Чужой объект
        ])
    
    def retrieve(self, request, pk=None):
        # Пример обработки запроса конкретного объекта
        # Здесь можно добавить дополнительную логику проверки прав
        return Response({
            'id': pk,
            'name': f'Test Object {pk}',
            'owner': request.user.id
        })
    
    def create(self, request):
        # Пример создания нового объекта
        # Проверка create_permission происходит через CustomPermission
        return Response({
            'id': 999,
            'name': request.data.get('name', 'New Object'),
            'owner': request.user.id
        }, status=status.HTTP_201_CREATED)