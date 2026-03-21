from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from .models import UserProfile, Address


class PersonalCenterTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='TestP@ss1234!', email='test@example.com')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_get_profile(self):
        resp = self.client.get('/api/account/profile/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['username'], 'testuser')

    def test_update_profile(self):
        resp = self.client.patch('/api/account/profile/', {'email': 'new@example.com', 'phone': '13800138000'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@example.com')

    def test_change_password_success(self):
        resp = self.client.post('/api/account/change-password/', {
            'old_password': 'TestP@ss1234!',
            'new_password': 'NewSecureP@ss9!',
            'confirm_password': 'NewSecureP@ss9!'
        }, format='json')
        self.assertEqual(resp.status_code, 200)

    def test_change_password_wrong_old(self):
        resp = self.client.post('/api/account/change-password/', {
            'old_password': 'WrongP@ss!',
            'new_password': 'NewSecureP@ss9!',
            'confirm_password': 'NewSecureP@ss9!'
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_change_password_mismatch(self):
        resp = self.client.post('/api/account/change-password/', {
            'old_password': 'TestP@ss1234!',
            'new_password': 'NewSecureP@ss9!',
            'confirm_password': 'DifferentP@ss9!'
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_address_crud(self):
        # Create
        resp = self.client.post('/api/account/addresses/', {
            'recipient_name': '张三',
            'phone': '13800138000',
            'province': '北京',
            'city': '北京市',
            'district': '朝阳区',
            'detail': '某某街道1号',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        addr_id = resp.data['id']

        # List
        resp = self.client.get('/api/account/addresses/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

        # Update
        resp = self.client.patch(f'/api/account/addresses/{addr_id}/', {'detail': '某某街道2号'}, format='json')
        self.assertEqual(resp.status_code, 200)

        # Set default
        resp = self.client.patch(f'/api/account/addresses/{addr_id}/set-default/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['is_default'])

        # Delete
        resp = self.client.delete(f'/api/account/addresses/{addr_id}/')
        self.assertEqual(resp.status_code, 204)

    def test_address_isolation(self):
        other_user = User.objects.create_user('other', password='TestP@ss1234!')
        other_token = Token.objects.create(user=other_user)
        Address.objects.create(
            user=other_user, recipient_name='李四', phone='13900139000',
            detail='其他地址', is_default=False
        )
        resp = self.client.get('/api/account/addresses/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 0)


class AdminAPITest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', password='AdminP@ss1234!', email='admin@example.com')
        self.user = User.objects.create_user('regular', password='UserP@ss1234!')
        self.admin_token = Token.objects.create(user=self.admin)
        self.user_token = Token.objects.create(user=self.user)
        self.client = APIClient()

    def test_stats_requires_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user_token.key}')
        resp = self.client.get('/api/account/admin/stats/')
        self.assertEqual(resp.status_code, 403)

    def test_stats_as_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        resp = self.client.get('/api/account/admin/stats/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('total_users', resp.data)
        self.assertIn('total_products', resp.data)
        self.assertIn('total_orders', resp.data)

    def test_admin_user_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        resp = self.client.get('/api/account/admin/users/')
        self.assertEqual(resp.status_code, 200)

    def test_admin_user_search(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        resp = self.client.get('/api/account/admin/users/?keyword=regular')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['username'], 'regular')
