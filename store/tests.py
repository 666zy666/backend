from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from .models import Product, Order, Category


class OrderStatusFlowTest(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user('buyer', password='pass123')
        self.seller = User.objects.create_user('seller', password='pass123')
        cat = Category.objects.create(name='测试分类')
        self.product = Product.objects.create(
            title='测试商品', price='100.00', seller=self.seller, category=cat
        )
        self.buyer_token = Token.objects.create(user=self.buyer)
        self.seller_token = Token.objects.create(user=self.seller)
        self.client = APIClient()

    def _make_order(self):
        return Order.objects.create(
            buyer=self.buyer, seller=self.seller,
            product=self.product, price=self.product.price,
            status=Order.STATUS_PENDING_PAYMENT
        )

    def test_pay_order_success(self):
        order = self._make_order()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}')
        resp = self.client.post(f'/api/store/orders/{order.pk}/pay/')
        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PENDING_RECEIPT)

    def test_pay_order_invalid_state(self):
        order = self._make_order()
        order.status = Order.STATUS_PENDING_RECEIPT
        order.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}')
        resp = self.client.post(f'/api/store/orders/{order.pk}/pay/')
        self.assertEqual(resp.status_code, 400)

    def test_cancel_order_success(self):
        order = self._make_order()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}')
        resp = self.client.post(f'/api/store/orders/{order.pk}/cancel/')
        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_CANCELLED)

    def test_cancel_order_invalid_state(self):
        order = self._make_order()
        order.status = Order.STATUS_PENDING_RECEIPT
        order.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}')
        resp = self.client.post(f'/api/store/orders/{order.pk}/cancel/')
        self.assertEqual(resp.status_code, 400)

    def test_confirm_receipt_success(self):
        order = self._make_order()
        order.status = Order.STATUS_PENDING_RECEIPT
        order.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}')
        resp = self.client.post(f'/api/store/orders/{order.pk}/confirm/')
        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_COMPLETED)

    def test_confirm_receipt_invalid_state(self):
        order = self._make_order()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}')
        resp = self.client.post(f'/api/store/orders/{order.pk}/confirm/')
        self.assertEqual(resp.status_code, 400)

    def test_my_orders_status_filter(self):
        order1 = self._make_order()
        order2 = self._make_order()
        order2.status = Order.STATUS_COMPLETED
        order2.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}')
        resp = self.client.get('/api/store/orders/my/?status=completed')
        self.assertEqual(resp.status_code, 200)
        ids = [o['id'] for o in resp.data]
        self.assertIn(order2.pk, ids)
        self.assertNotIn(order1.pk, ids)

    def test_order_serializer_has_status_display(self):
        order = self._make_order()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}')
        resp = self.client.get('/api/store/orders/my/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('status_display', resp.data[0])
        self.assertEqual(resp.data[0]['status_display'], '待付款')

    def test_seller_cancel_validates_state(self):
        order = self._make_order()
        order.status = Order.STATUS_PENDING_RECEIPT
        order.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller_token.key}')
        resp = self.client.patch(f'/api/store/orders/{order.pk}/', {'action': 'cancel'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_seller_ship_validates_state(self):
        # ship requires PENDING_RECEIPT state; should fail when order is in PENDING_PAYMENT
        order = self._make_order()  # pending_payment
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller_token.key}')
        resp = self.client.patch(f'/api/store/orders/{order.pk}/', {'action': 'ship'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_seller_ship_on_pending_receipt(self):
        order = self._make_order()
        order.status = Order.STATUS_PENDING_RECEIPT
        order.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller_token.key}')
        resp = self.client.patch(f'/api/store/orders/{order.pk}/', {
            'action': 'ship',
            'tracking_number': 'SF123456',
            'shipping_company': '顺丰'
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.tracking_number, 'SF123456')
