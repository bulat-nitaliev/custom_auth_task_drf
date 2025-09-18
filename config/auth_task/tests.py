import json
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import User, Role, BusinessElement, AccessRule
import factory
from faker import Faker

fake = Faker()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    email = factory.LazyAttribute(lambda _: fake.email())
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())
    password = factory.PostGeneration(lambda obj, *args, **kwargs: obj.set_password('testpass123'))

class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role
    
    name = factory.LazyAttribute(lambda _: fake.word())
    description = factory.LazyAttribute(lambda _: fake.sentence())

class BusinessElementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BusinessElement
    
    name = factory.LazyAttribute(lambda _: fake.word())
    description = factory.LazyAttribute(lambda _: fake.sentence())

class AccessRuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AccessRule
    
    role = factory.SubFactory(RoleFactory)
    element = factory.SubFactory(BusinessElementFactory)
    read_permission = True
    read_all_permission = False
    create_permission = False
    update_permission = False
    update_all_permission = False
    delete_permission = False
    delete_all_permission = False


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'patronymic': 'Smith',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        self.url = '/api/users/register/'

    def test_user_registration(self):
        """Тест успешной регистрации пользователя"""
        # url = reverse('user-register')
        
        response = self.client.post(self.url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'test@example.com')

    def test_user_registration_password_mismatch(self):
        """Тест регистрации с несовпадающими паролями"""
        data = self.user_data.copy()
        data['password_confirm'] = 'differentpassword'
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_user_login(self):
        """Тест успешного входа пользователя"""
        user = UserFactory()
        user.set_password('testpass123')
        user.save()
        
        url = '/api/users/login/'
        data = {
            'email': user.email,
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

class AuthorizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.headers = {}
        
        self.admin_role = RoleFactory(name='admin')
        self.user_role = RoleFactory(name='user')
        
        self.mock_element = BusinessElementFactory(name='mock_data')
        
        self.admin_rule = AccessRuleFactory(
            role=self.admin_role,
            element=self.mock_element,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            update_all_permission=True,
            delete_permission=True,
            delete_all_permission=True
        )
        
        self.user_rule = AccessRuleFactory(
            role=self.user_role,
            element=self.mock_element,
            read_permission=True,
            read_all_permission=False,
            create_permission=False,
            update_permission=False,
            update_all_permission=False,
            delete_permission=False,
            delete_all_permission=False
        )
        
        self.admin_user = UserFactory(role=self.admin_role)
        self.admin_user.set_password('testpass123')
        self.admin_user.save()
        
        self.regular_user = UserFactory(role=self.user_role)
        self.regular_user.set_password('testpass123')
        self.regular_user.save()

    def test_admin_access_to_mock_data(self):
        """Тест доступа администратора к mock-данным"""
        login_url = '/api/users/login/'
        login_data = {
            'email': self.admin_user.email,
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        token = login_response.data['token']
        # print(token)
        headers = {}
        headers["Authorization"] =  f'Bearer {token}'
        # self.client.force_authenticate(user=self.admin_user)
        mock_data_url = '/api/mock-data/'
        response = self.client.get(mock_data_url,headers=headers, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_access_to_mock_data(self):
        """Тест доступа обычного пользователя к mock-данным"""
        login_url = '/api/users/login/'
        login_data = {
            'email': self.regular_user.email,
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        token = login_response.data['token']
        headers = {}
        headers["Authorization"] =  f'Bearer {token}'
        
       
        mock_data_url = '/api/mock-data/'
        response = self.client.get(mock_data_url, headers=headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthorized_access_to_mock_data(self):
        """Тест доступа к mock-данным без авторизации"""
        mock_data_url = '/api/mock-data/'
        response = self.client.get(mock_data_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class UserManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.user.set_password('testpass123')
        self.user.save()
        
        login_url = '/api/users/login/'
        login_data = {
            'email': self.user.email,
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.token = login_response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_get_user_profile(self):
        """Тест получения профиля пользователя"""
        url = f'/api/users/{self.user.pk}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_update_user_profile(self):
        """Тест обновления профиля пользователя"""
        url = f'/api/users/{self.user.pk}/'
        update_data = {
            'first_name': 'UpdatedName',
            'last_name': 'UpdatedLastName'
        }
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'UpdatedName')
        self.assertEqual(self.user.last_name, 'UpdatedLastName')

    def test_delete_user(self):
        """Тест мягкого удаления пользователя"""
        url = f'/api/users/{self.user.pk}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)