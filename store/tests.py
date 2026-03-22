from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from store.models import Order, Product, Category
from account.models import Address


def make_user(username='buyer', password='pass1234', is_staff=False):
    user = User.objects.create_user(username=username, password=password)
    user.is_staff = is_staff
    user.save()
    return user


def make_product(seller):
    cat = Category.objects.create(name='Test')
    return Product.objects.create(
        title='Test Product', price='100.00', seller=seller, category=cat
    )


class OrderStatusTransitionTests(TestCase):
    """Order state-machine transition rules."""

    def setUp(self):
        self.buyer = make_user('buyer_t')
        self.seller = make_user('seller_t')
        self.product = make_product(self.seller)
        self.client = APIClient()

    def _make_order(self, status=Order.STATUS_PENDING_PAYMENT):
        import uuid
        return Order.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            product=self.product,
            price=self.product.price,
            status=status,
            order_no=f"ORD{uuid.uuid4().hex[:16].upper()}",
        )

    # --- can_transition_to helper ---
    def test_pending_payment_can_pay(self):
        order = self._make_order(Order.STATUS_PENDING_PAYMENT)
        self.assertTrue(order.can_transition_to(Order.STATUS_PENDING_SHIPMENT))

    def test_pending_payment_can_cancel(self):
        order = self._make_order(Order.STATUS_PENDING_PAYMENT)
        self.assertTrue(order.can_transition_to(Order.STATUS_CANCELLED))

    def test_pending_payment_cannot_complete(self):
        order = self._make_order(Order.STATUS_PENDING_PAYMENT)
        self.assertFalse(order.can_transition_to(Order.STATUS_COMPLETED))

    def test_pending_shipment_can_ship(self):
        order = self._make_order(Order.STATUS_PENDING_SHIPMENT)
        self.assertTrue(order.can_transition_to(Order.STATUS_PENDING_RECEIPT))

    def test_pending_shipment_cannot_cancel(self):
        order = self._make_order(Order.STATUS_PENDING_SHIPMENT)
        self.assertFalse(order.can_transition_to(Order.STATUS_CANCELLED))

    def test_pending_receipt_can_confirm(self):
        order = self._make_order(Order.STATUS_PENDING_RECEIPT)
        self.assertTrue(order.can_transition_to(Order.STATUS_COMPLETED))

    def test_completed_no_transitions(self):
        order = self._make_order(Order.STATUS_COMPLETED)
        for s in [Order.STATUS_CANCELLED, Order.STATUS_PENDING_SHIPMENT,
                  Order.STATUS_PENDING_RECEIPT]:
            self.assertFalse(order.can_transition_to(s))

    # --- API endpoint checks ---
    def test_pay_transitions_to_pending_shipment(self):
        order = self._make_order(Order.STATUS_PENDING_PAYMENT)
        self.client.force_authenticate(self.buyer)
        r = self.client.post(f'/api/store/orders/{order.pk}/pay/')
        self.assertEqual(r.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PENDING_SHIPMENT)
        self.assertIsNotNone(order.paid_at)

    def test_pay_invalid_state_returns_400(self):
        order = self._make_order(Order.STATUS_PENDING_RECEIPT)
        self.client.force_authenticate(self.buyer)
        r = self.client.post(f'/api/store/orders/{order.pk}/pay/')
        self.assertEqual(r.status_code, 400)

    def test_cancel_sets_cancel_time(self):
        order = self._make_order(Order.STATUS_PENDING_PAYMENT)
        self.client.force_authenticate(self.buyer)
        r = self.client.post(f'/api/store/orders/{order.pk}/cancel/')
        self.assertEqual(r.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_CANCELLED)
        self.assertIsNotNone(order.cancel_time)

    def test_cancel_invalid_state_returns_400(self):
        order = self._make_order(Order.STATUS_PENDING_SHIPMENT)
        self.client.force_authenticate(self.buyer)
        r = self.client.post(f'/api/store/orders/{order.pk}/cancel/')
        self.assertEqual(r.status_code, 400)

    def test_confirm_receipt_invalid_state_returns_400(self):
        order = self._make_order(Order.STATUS_PENDING_SHIPMENT)
        self.client.force_authenticate(self.buyer)
        r = self.client.post(f'/api/store/orders/{order.pk}/confirm/')
        self.assertEqual(r.status_code, 400)

    def test_confirm_receipt_transitions_to_completed(self):
        order = self._make_order(Order.STATUS_PENDING_RECEIPT)
        self.client.force_authenticate(self.buyer)
        r = self.client.post(f'/api/store/orders/{order.pk}/confirm/')
        self.assertEqual(r.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_COMPLETED)


class AdminOrderShipTests(TestCase):
    """Admin ship action: PENDING_SHIPMENT → PENDING_RECEIPT."""

    def setUp(self):
        self.buyer = make_user('buyer_s')
        self.seller = make_user('seller_s')
        self.admin = make_user('admin_s', is_staff=True)
        self.product = make_product(self.seller)
        self.client = APIClient()

    def _make_order(self, status=Order.STATUS_PENDING_SHIPMENT):
        import uuid
        return Order.objects.create(
            buyer=self.buyer, seller=self.seller, product=self.product,
            price=self.product.price, status=status,
            order_no=f"ORD{uuid.uuid4().hex[:16].upper()}",
        )

    def test_admin_ship_success(self):
        order = self._make_order(Order.STATUS_PENDING_SHIPMENT)
        self.client.force_authenticate(self.admin)
        r = self.client.post(f'/api/store/orders/{order.pk}/ship/', {
            'tracking_number': 'SF1234567',
            'shipping_company': '顺丰速运',
        })
        self.assertEqual(r.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PENDING_RECEIPT)
        self.assertEqual(order.tracking_number, 'SF1234567')
        self.assertIsNotNone(order.shipped_at)

    def test_non_admin_cannot_ship(self):
        order = self._make_order(Order.STATUS_PENDING_SHIPMENT)
        self.client.force_authenticate(self.buyer)
        r = self.client.post(f'/api/store/orders/{order.pk}/ship/', {})
        self.assertEqual(r.status_code, 403)

    def test_ship_wrong_status_returns_400(self):
        order = self._make_order(Order.STATUS_PENDING_PAYMENT)
        self.client.force_authenticate(self.admin)
        r = self.client.post(f'/api/store/orders/{order.pk}/ship/', {})
        self.assertEqual(r.status_code, 400)


class PasswordChangeTests(TestCase):
    """Password change with old-password verification."""

    def setUp(self):
        self.user = make_user('pwd_user', password='oldpass123')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_change_password_success(self):
        r = self.client.post('/api/account/change-password/', {
            'old_password': 'oldpass123',
            'new_password': 'NewPass456!',
            'confirm_password': 'NewPass456!',
        })
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass456!'))

    def test_wrong_old_password_rejected(self):
        r = self.client.post('/api/account/change-password/', {
            'old_password': 'wrongpass',
            'new_password': 'NewPass456!',
            'confirm_password': 'NewPass456!',
        })
        self.assertEqual(r.status_code, 400)

    def test_mismatched_new_passwords_rejected(self):
        r = self.client.post('/api/account/change-password/', {
            'old_password': 'oldpass123',
            'new_password': 'NewPass456!',
            'confirm_password': 'different!',
        })
        self.assertEqual(r.status_code, 400)


class DefaultAddressUniquenessTests(TestCase):
    """Only one default address per user."""

    def setUp(self):
        self.user = make_user('addr_user')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _create_address(self, recipient='张三', is_default=False):
        return Address.objects.create(
            user=self.user,
            recipient_name=recipient,
            phone='13800138000',
            province='广东',
            city='深圳',
            district='南山',
            detail='科技园路1号',
            is_default=is_default,
        )

    def test_set_default_clears_previous_default(self):
        a1 = self._create_address('A', is_default=True)
        a2 = self._create_address('B', is_default=False)

        r = self.client.patch(f'/api/account/addresses/{a2.pk}/set-default/')
        self.assertEqual(r.status_code, 200)

        a1.refresh_from_db()
        a2.refresh_from_db()
        self.assertFalse(a1.is_default)
        self.assertTrue(a2.is_default)

    def test_only_one_default_at_a_time(self):
        addresses = [self._create_address(f'User{i}') for i in range(3)]
        for addr in addresses:
            self.client.patch(f'/api/account/addresses/{addr.pk}/set-default/')

        defaults = Address.objects.filter(user=self.user, is_default=True)
        self.assertEqual(defaults.count(), 1)
        self.assertEqual(defaults.first().pk, addresses[-1].pk)

