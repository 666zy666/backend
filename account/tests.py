"""
Tests for the Admin management API.

Covers:
- Permission interception (non-admin is rejected with 403)
- Dashboard overview and trend
- User management (list, detail, create, patch, delete)
- Product management (list, detail, create, put, delete)
- Order management (list, detail, patch status, delete/cancel)
- Banner management (list, create, detail, update, delete)
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from store.models import Category, Product, Order, Banner


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(username, password='pass1234', is_staff=False):
    user = User.objects.create_user(username=username, password=password)
    user.is_staff = is_staff
    user.save()
    return user


def make_product(seller, title='Test Product', price='100.00'):
    cat, _ = Category.objects.get_or_create(name='TestCat')
    return Product.objects.create(
        title=title, price=price, seller=seller, category=cat
    )


def make_order(buyer, seller, product, status=Order.STATUS_PENDING_PAYMENT):
    import uuid
    return Order.objects.create(
        buyer=buyer,
        seller=seller,
        product=product,
        price=product.price,
        status=status,
        order_no=f"ORD{uuid.uuid4().hex[:16].upper()}",
    )


# ── Permission interception ───────────────────────────────────────────────────

class AdminPermissionTests(TestCase):
    """Non-admin requests must be rejected."""

    def setUp(self):
        self.regular_user = make_user('regular')
        self.admin_user = make_user('admin', is_staff=True)
        self.client = APIClient()

    def test_unauthenticated_dashboard_returns_401(self):
        r = self.client.get('/api/admin/dashboard/overview/')
        self.assertIn(r.status_code, [401, 403])

    def test_regular_user_dashboard_returns_403(self):
        self.client.force_authenticate(self.regular_user)
        r = self.client.get('/api/admin/dashboard/overview/')
        self.assertEqual(r.status_code, 403)

    def test_admin_user_dashboard_returns_200(self):
        self.client.force_authenticate(self.admin_user)
        r = self.client.get('/api/admin/dashboard/overview/')
        self.assertEqual(r.status_code, 200)

    def test_regular_user_users_list_returns_403(self):
        self.client.force_authenticate(self.regular_user)
        r = self.client.get('/api/admin/users/')
        self.assertEqual(r.status_code, 403)

    def test_regular_user_products_list_returns_403(self):
        self.client.force_authenticate(self.regular_user)
        r = self.client.get('/api/admin/products/')
        self.assertEqual(r.status_code, 403)

    def test_regular_user_orders_list_returns_403(self):
        self.client.force_authenticate(self.regular_user)
        r = self.client.get('/api/admin/orders/')
        self.assertEqual(r.status_code, 403)


# ── Admin auth ────────────────────────────────────────────────────────────────

class AdminAuthTests(TestCase):
    def setUp(self):
        self.admin = make_user('auth_admin', password='adminpass', is_staff=True)
        self.regular = make_user('auth_user', password='userpass')
        self.client = APIClient()

    def test_admin_login_success(self):
        r = self.client.post('/api/admin/auth/login/', {
            'username': 'auth_admin',
            'password': 'adminpass',
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn('token', r.data)
        self.assertTrue(r.data['is_staff'])

    def test_non_admin_login_rejected_403(self):
        r = self.client.post('/api/admin/auth/login/', {
            'username': 'auth_user',
            'password': 'userpass',
        })
        self.assertEqual(r.status_code, 403)

    def test_wrong_password_rejected_400(self):
        r = self.client.post('/api/admin/auth/login/', {
            'username': 'auth_admin',
            'password': 'wrongpassword',
        })
        self.assertEqual(r.status_code, 400)

    def test_admin_me_returns_info(self):
        self.client.force_authenticate(self.admin)
        r = self.client.get('/api/admin/auth/me/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['username'], 'auth_admin')
        self.assertTrue(r.data['is_staff'])


# ── Dashboard ─────────────────────────────────────────────────────────────────

class AdminDashboardTests(TestCase):
    def setUp(self):
        self.admin = make_user('dash_admin', is_staff=True)
        self.buyer = make_user('dash_buyer')
        self.seller = make_user('dash_seller')
        self.product = make_product(self.seller)
        make_order(self.buyer, self.seller, self.product)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_overview_returns_expected_keys(self):
        r = self.client.get('/api/admin/dashboard/overview/')
        self.assertEqual(r.status_code, 200)
        for key in ('total_users', 'total_products', 'total_orders',
                    'today_new_users', 'today_orders', 'today_revenue',
                    'total_revenue', 'order_status_counts'):
            self.assertIn(key, r.data, msg=f"Missing key: {key}")

    def test_overview_counts_are_integers(self):
        r = self.client.get('/api/admin/dashboard/overview/')
        self.assertIsInstance(r.data['total_users'], int)
        self.assertIsInstance(r.data['total_orders'], int)

    def test_total_users_at_least_three(self):
        r = self.client.get('/api/admin/dashboard/overview/')
        self.assertGreaterEqual(r.data['total_users'], 3)  # admin + buyer + seller


# ── User management ───────────────────────────────────────────────────────────

class AdminUserTests(TestCase):
    def setUp(self):
        self.admin = make_user('user_admin', is_staff=True)
        self.u1 = make_user('alice')
        self.u2 = make_user('bob')
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_list_returns_paginated(self):
        r = self.client.get('/api/admin/users/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('count', r.data)
        self.assertIn('results', r.data)
        self.assertGreaterEqual(r.data['count'], 3)  # admin + alice + bob

    def test_list_keyword_filter(self):
        r = self.client.get('/api/admin/users/?keyword=alice')
        self.assertEqual(r.status_code, 200)
        usernames = [u['username'] for u in r.data['results']]
        self.assertIn('alice', usernames)
        self.assertNotIn('bob', usernames)

    def test_list_status_filter_active(self):
        self.u2.is_active = False
        self.u2.save()
        r = self.client.get('/api/admin/users/?status=active')
        usernames = [u['username'] for u in r.data['results']]
        self.assertNotIn('bob', usernames)

    def test_detail_returns_user(self):
        r = self.client.get(f'/api/admin/users/{self.u1.pk}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['username'], 'alice')

    def test_detail_nonexistent_returns_404(self):
        r = self.client.get('/api/admin/users/99999/')
        self.assertEqual(r.status_code, 404)

    def test_patch_is_active(self):
        r = self.client.patch(
            f'/api/admin/users/{self.u1.pk}/',
            {'is_active': False},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.u1.refresh_from_db()
        self.assertFalse(self.u1.is_active)

    def test_patch_is_staff(self):
        r = self.client.patch(
            f'/api/admin/users/{self.u1.pk}/',
            {'is_staff': True},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.u1.refresh_from_db()
        self.assertTrue(self.u1.is_staff)


# ── Product management ────────────────────────────────────────────────────────

class AdminProductTests(TestCase):
    def setUp(self):
        self.admin = make_user('prod_admin', is_staff=True)
        self.seller = make_user('prod_seller')
        self.product = make_product(self.seller, title='Widget A')
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_list_returns_paginated(self):
        r = self.client.get('/api/admin/products/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('count', r.data)
        self.assertIn('results', r.data)

    def test_list_keyword_filter(self):
        make_product(self.seller, title='Gadget B')
        r = self.client.get('/api/admin/products/?keyword=Widget')
        titles = [p['title'] for p in r.data['results']]
        self.assertIn('Widget A', titles)
        self.assertNotIn('Gadget B', titles)

    def test_list_status_filter_inactive(self):
        self.product.is_active = False
        self.product.save()
        r = self.client.get('/api/admin/products/?status=inactive')
        self.assertGreaterEqual(r.data['count'], 1)

    def test_detail_returns_product(self):
        r = self.client.get(f'/api/admin/products/{self.product.pk}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['title'], 'Widget A')

    def test_put_updates_title(self):
        r = self.client.put(
            f'/api/admin/products/{self.product.pk}/',
            {'title': 'Widget A Updated', 'price': '200.00'},
        )
        self.assertEqual(r.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.title, 'Widget A Updated')

    def test_delete_deactivates_product(self):
        r = self.client.delete(f'/api/admin/products/{self.product.pk}/')
        self.assertEqual(r.status_code, 200)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)


# ── Order management ──────────────────────────────────────────────────────────

class AdminOrderTests(TestCase):
    def setUp(self):
        self.admin = make_user('ord_admin', is_staff=True)
        self.buyer = make_user('ord_buyer')
        self.seller = make_user('ord_seller')
        self.product = make_product(self.seller)
        self.order = make_order(self.buyer, self.seller, self.product)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_list_returns_paginated(self):
        r = self.client.get('/api/admin/orders/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('count', r.data)
        self.assertIn('results', r.data)

    def test_list_status_filter(self):
        r = self.client.get(f'/api/admin/orders/?status={Order.STATUS_PENDING_PAYMENT}')
        statuses = [o['status'] for o in r.data['results']]
        self.assertTrue(all(s == Order.STATUS_PENDING_PAYMENT for s in statuses))

    def test_list_keyword_filter_by_buyer(self):
        r = self.client.get('/api/admin/orders/?keyword=ord_buyer')
        self.assertGreaterEqual(r.data['count'], 1)

    def test_detail_returns_order(self):
        r = self.client.get(f'/api/admin/orders/{self.order.pk}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['id'], self.order.pk)

    def test_detail_nonexistent_returns_404(self):
        r = self.client.get('/api/admin/orders/99999/')
        self.assertEqual(r.status_code, 404)

    def test_patch_status_valid_transition(self):
        r = self.client.patch(
            f'/api/admin/orders/{self.order.pk}/status/',
            {'status': Order.STATUS_PENDING_SHIPMENT},
        )
        self.assertEqual(r.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PENDING_SHIPMENT)

    def test_patch_status_invalid_value_returns_400(self):
        r = self.client.patch(
            f'/api/admin/orders/{self.order.pk}/status/',
            {'status': 'nonexistent_status'},
        )
        self.assertEqual(r.status_code, 400)

    def test_patch_status_missing_field_returns_400(self):
        r = self.client.patch(f'/api/admin/orders/{self.order.pk}/status/', {})
        self.assertEqual(r.status_code, 400)

    def test_patch_status_sets_shipped_at(self):
        self.order.status = Order.STATUS_PENDING_SHIPMENT
        self.order.save()
        r = self.client.patch(
            f'/api/admin/orders/{self.order.pk}/status/',
            {'status': Order.STATUS_PENDING_RECEIPT, 'tracking_number': 'SF999'},
        )
        self.assertEqual(r.status_code, 200)
        self.order.refresh_from_db()
        self.assertIsNotNone(self.order.shipped_at)
        self.assertEqual(self.order.tracking_number, 'SF999')

    def test_patch_status_nonexistent_order_returns_404(self):
        r = self.client.patch(
            '/api/admin/orders/99999/status/',
            {'status': Order.STATUS_CANCELLED},
        )
        self.assertEqual(r.status_code, 404)


# ── Dashboard trend ───────────────────────────────────────────────────────────

class AdminDashboardTrendTests(TestCase):
    def setUp(self):
        self.admin = make_user('trend_admin', is_staff=True)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_trend_returns_7_days(self):
        r = self.client.get('/api/admin/dashboard/trend/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('trend', r.data)
        self.assertEqual(len(r.data['trend']), 7)

    def test_trend_day_has_expected_keys(self):
        r = self.client.get('/api/admin/dashboard/trend/')
        day = r.data['trend'][0]
        for key in ('date', 'order_count', 'revenue'):
            self.assertIn(key, day)

    def test_trend_requires_admin(self):
        regular = make_user('trend_regular')
        self.client.force_authenticate(regular)
        r = self.client.get('/api/admin/dashboard/trend/')
        self.assertEqual(r.status_code, 403)


# ── User create / delete ──────────────────────────────────────────────────────

class AdminUserCreateDeleteTests(TestCase):
    def setUp(self):
        self.admin = make_user('ucreate_admin', is_staff=True)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_create_user_success(self):
        r = self.client.post('/api/admin/users/', {
            'username': 'newbie',
            'password': 'securepass',
            'email': 'newbie@example.com',
        }, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['username'], 'newbie')
        self.assertTrue(User.objects.filter(username='newbie').exists())

    def test_create_user_duplicate_username_returns_400(self):
        make_user('dup_user')
        r = self.client.post('/api/admin/users/', {
            'username': 'dup_user',
            'password': 'pass',
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_create_user_missing_username_returns_400(self):
        r = self.client.post('/api/admin/users/', {'password': 'pass'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_create_user_missing_password_returns_400(self):
        r = self.client.post('/api/admin/users/', {'username': 'nopass'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_delete_user_success(self):
        target = make_user('to_delete')
        r = self.client.delete(f'/api/admin/users/{target.pk}/')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(pk=target.pk).exists())

    def test_delete_self_returns_400(self):
        r = self.client.delete(f'/api/admin/users/{self.admin.pk}/')
        self.assertEqual(r.status_code, 400)

    def test_delete_nonexistent_returns_404(self):
        r = self.client.delete('/api/admin/users/99999/')
        self.assertEqual(r.status_code, 404)

    def test_patch_email_and_username(self):
        target = make_user('patch_target')
        r = self.client.patch(
            f'/api/admin/users/{target.pk}/',
            {'email': 'new@example.com', 'username': 'patch_target_new'},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        target.refresh_from_db()
        self.assertEqual(target.email, 'new@example.com')
        self.assertEqual(target.username, 'patch_target_new')


# ── Order cancel / delete ─────────────────────────────────────────────────────

class AdminOrderCancelDeleteTests(TestCase):
    def setUp(self):
        self.admin = make_user('ocancel_admin', is_staff=True)
        self.buyer = make_user('ocancel_buyer')
        self.seller = make_user('ocancel_seller')
        self.product = make_product(self.seller)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_delete_pending_order_cancels_it(self):
        order = make_order(self.buyer, self.seller, self.product)
        r = self.client.delete(f'/api/admin/orders/{order.pk}/')
        self.assertEqual(r.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_CANCELLED)
        self.assertIsNotNone(order.cancel_time)

    def test_delete_already_cancelled_order_removes_it(self):
        order = make_order(self.buyer, self.seller, self.product, status=Order.STATUS_CANCELLED)
        pk = order.pk
        r = self.client.delete(f'/api/admin/orders/{pk}/')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Order.objects.filter(pk=pk).exists())

    def test_delete_completed_order_returns_400(self):
        order = make_order(self.buyer, self.seller, self.product, status=Order.STATUS_COMPLETED)
        r = self.client.delete(f'/api/admin/orders/{order.pk}/')
        self.assertEqual(r.status_code, 400)

    def test_delete_nonexistent_returns_404(self):
        r = self.client.delete('/api/admin/orders/99999/')
        self.assertEqual(r.status_code, 404)


# ── Banner management ─────────────────────────────────────────────────────────

class AdminBannerTests(TestCase):
    def setUp(self):
        self.admin = make_user('banner_admin', is_staff=True)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.banner = Banner.objects.create(title='Test Banner', order=1, is_active=True)

    def test_list_returns_paginated(self):
        r = self.client.get('/api/admin/banners/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('count', r.data)
        self.assertIn('results', r.data)
        self.assertGreaterEqual(r.data['count'], 1)

    def test_list_filter_by_active(self):
        Banner.objects.create(title='Inactive Banner', order=2, is_active=False)
        r = self.client.get('/api/admin/banners/?is_active=true')
        self.assertEqual(r.status_code, 200)
        for item in r.data['results']:
            self.assertTrue(item['is_active'])

    def test_detail_returns_banner(self):
        r = self.client.get(f'/api/admin/banners/{self.banner.pk}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['title'], 'Test Banner')

    def test_detail_nonexistent_returns_404(self):
        r = self.client.get('/api/admin/banners/99999/')
        self.assertEqual(r.status_code, 404)

    def test_put_updates_title_and_is_active(self):
        r = self.client.put(
            f'/api/admin/banners/{self.banner.pk}/',
            {'title': 'Updated Banner', 'is_active': False},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.banner.refresh_from_db()
        self.assertEqual(self.banner.title, 'Updated Banner')
        self.assertFalse(self.banner.is_active)

    def test_delete_banner(self):
        pk = self.banner.pk
        r = self.client.delete(f'/api/admin/banners/{pk}/')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Banner.objects.filter(pk=pk).exists())

    def test_delete_nonexistent_returns_404(self):
        r = self.client.delete('/api/admin/banners/99999/')
        self.assertEqual(r.status_code, 404)

    def test_banner_requires_admin(self):
        regular = make_user('banner_regular')
        self.client.force_authenticate(regular)
        r = self.client.get('/api/admin/banners/')
        self.assertEqual(r.status_code, 403)
