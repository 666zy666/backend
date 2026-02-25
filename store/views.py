# store/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Category, Product, ProductImage, Favorite, Order
from .serializers import CategorySerializer, ProductSerializer, FavoriteSerializer, OrderSerializer
import uuid

class ProductListCreate(generics.ListCreateAPIView):
    queryset = Product.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("请先登录")
        product = serializer.save(seller=self.request.user)
        images_data = self.request.FILES.getlist('images')
        for image in images_data:
            ProductImage.objects.create(product=product, image=image)

class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        return {'request': self.request}

class MyProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(seller=request.user).order_by('-created_at')
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

class FavoriteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = Favorite.objects.filter(user=request.user).order_by('-created_at')
        serializer = FavoriteSerializer(favorites, many=True, context={'request': request})
        return Response(serializer.data)

class FavoriteCreateDestroyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"detail": "缺少product_id"}, status=400)
        product = get_object_or_404(Product, id=product_id)
        if Favorite.objects.filter(user=request.user, product=product).exists():
            return Response({"detail": "已收藏"}, status=400)
        favorite = Favorite.objects.create(user=request.user, product=product)
        serializer = FavoriteSerializer(favorite, context={'request': request})
        return Response(serializer.data, status=201)

    def delete(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"detail": "缺少product_id"}, status=400)
        favorite = Favorite.objects.filter(user=request.user, product_id=product_id)
        if not favorite.exists():
            return Response({"detail": "未收藏"}, status=404)
        favorite.delete()
        return Response({"detail": "已取消收藏"}, status=204)

# 新增: 我的订单（买家视角）
class MyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)

# 新增: 待处理订单（卖家视角）
class SellerOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(seller=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)

# 新增: 订单创建
class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"detail": "缺少product_id"}, status=400)
        product = get_object_or_404(Product, id=product_id)
        if product.seller == request.user:
            return Response({"detail": "不能购买自己的商品"}, status=400)
        order = Order.objects.create(
            buyer=request.user,
            seller=product.seller,
            product=product,
            price=product.price
        )
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data, status=201)

# 新增: 订单更新（卖家处理）
class OrderUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk, seller=request.user)
        action = request.data.get('action')
        if action == 'ship':
            order.status = 'shipped'
            order.shipped_at = timezone.now()
            order.shipping_company = request.data.get('shipping_company')
            order.tracking_number = request.data.get('tracking_number')
        elif action == 'complete':
            order.status = 'completed'
            order.completed_at = timezone.now()
        elif action == 'cancel':
            order.status = 'cancelled'
        else:
            return Response({"detail": "无效操作"}, status=400)
        order.save()
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data)


class SimulatePayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({"detail": "缺少 order_id"}, status=400)

        order = get_object_or_404(Order, id=order_id, buyer=request.user, status='pending')

        # 模拟支付成功
        order.status = 'paid'
        order.paid_at = timezone.now()
        order.transaction_id = f"SIM-{uuid.uuid4().hex[:16]}"  # 模拟交易号
        order.save()

        serializer = OrderSerializer(order, context={'request': request})
        return Response({
            "code": 0,
            "msg": "支付成功（模拟）",
            "data": serializer.data
        })