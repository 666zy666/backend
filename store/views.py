# store/views.py
from rest_framework import generics, status,serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Category, Product, ProductImage, Favorite, Order,Banner
from rest_framework.pagination import PageNumberPagination
from .serializers import CategorySerializer, ProductSerializer, FavoriteSerializer, OrderSerializer,BannerSerializer
import uuid
from django.db.models import Q

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

# 收藏商品
class FavoriteCreateView(generics.CreateAPIView):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        product = get_object_or_404(Product, id=product_id)
        # 避免重复收藏
        if Favorite.objects.filter(user=self.request.user, product=product).exists():
            raise serializers.ValidationError("已收藏")
        serializer.save(user=self.request.user, product=product)

# 取消收藏
class FavoriteDeleteView(generics.DestroyAPIView):
    queryset = Favorite.objects.all()
    permission_classes = [IsAuthenticated]

    def get_object(self):
        product_id = self.kwargs['product_id']
        return get_object_or_404(Favorite, user=self.request.user, product_id=product_id)

# 我的收藏列表
class FavoriteListView(generics.ListAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).order_by('-created_at')

# 新增: 我的订单（买家视角，支持状态筛选）
class MyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Order.objects.filter(buyer=request.user).order_by('-created_at')
        order_status = request.query_params.get('status', '').strip()
        if order_status:
            queryset = queryset.filter(status=order_status)
        serializer = OrderSerializer(queryset, many=True, context={'request': request})
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
            order.status = Order.STATUS_PENDING_RECEIPT
            order.shipped_at = timezone.now()
            order.shipping_company = request.data.get('shipping_company')
            order.tracking_number = request.data.get('tracking_number')
        elif action == 'complete':
            order.status = Order.STATUS_COMPLETED
            order.completed_at = timezone.now()
        elif action == 'cancel':
            order.status = Order.STATUS_CANCELLED
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

        # 兼容旧状态 'pending' 和新状态 'pending_payment'
        order = get_object_or_404(Order, id=order_id, buyer=request.user)
        if order.status not in ('pending', 'pending_payment'):
            return Response({"detail": "仅待付款订单可以支付"}, status=400)

        # 模拟支付成功
        order.status = Order.STATUS_PENDING_RECEIPT
        order.paid_at = timezone.now()
        order.transaction_id = f"SIM-{uuid.uuid4().hex[:16]}"  # 模拟交易号
        order.save()

        serializer = OrderSerializer(order, context={'request': request})
        return Response({
            "code": 0,
            "msg": "支付成功（模拟）",
            "data": serializer.data
        })


# ── 用户侧订单操作 ────────────────────────────────────────────

class OrderPayView(APIView):
    """订单支付：PENDING_PAYMENT → PENDING_RECEIPT"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, buyer=request.user)
        if order.status != Order.STATUS_PENDING_PAYMENT:
            return Response(
                {"detail": f"当前订单状态为「{order.get_status_display()}」，无法支付"},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = Order.STATUS_PENDING_RECEIPT
        order.paid_at = timezone.now()
        order.transaction_id = f"SIM-{uuid.uuid4().hex[:16]}"
        order.save()
        serializer = OrderSerializer(order, context={'request': request})
        return Response({"detail": "支付成功", "data": serializer.data})


class OrderCancelView(APIView):
    """取消订单：PENDING_PAYMENT → CANCELLED"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, buyer=request.user)
        if order.status != Order.STATUS_PENDING_PAYMENT:
            return Response(
                {"detail": f"当前订单状态为「{order.get_status_display()}」，无法取消"},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = Order.STATUS_CANCELLED
        order.save()
        serializer = OrderSerializer(order, context={'request': request})
        return Response({"detail": "订单已取消", "data": serializer.data})


class OrderConfirmView(APIView):
    """确认收货：PENDING_RECEIPT → COMPLETED"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, buyer=request.user)
        if order.status != Order.STATUS_PENDING_RECEIPT:
            return Response(
                {"detail": f"当前订单状态为「{order.get_status_display()}」，无法确认收货"},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = Order.STATUS_COMPLETED
        order.completed_at = timezone.now()
        order.save()
        serializer = OrderSerializer(order, context={'request': request})
        return Response({"detail": "确认收货成功，订单已完成", "data": serializer.data})

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class ProductSearchView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)


        # 关键词搜索
        keyword = self.request.query_params.get('keyword', '').strip()
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(description__icontains=keyword) |
                Q(brand__icontains=keyword) |
                Q(model_number__icontains=keyword) |
                Q(machinery_type__icontains=keyword)
            )

        # 分类筛选
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        # 价格区间（可选）
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # 排序
        sort = self.request.query_params.get('sort', '-created_at')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        else:
            queryset = queryset.order_by('-created_at')




        return queryset

class BannerListView(generics.ListAPIView):
    queryset = Banner.objects.filter(is_active=True).order_by('order')
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]



