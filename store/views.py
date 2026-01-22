# store/views.py - 完整视图代码
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Product, ProductImage, Category, Favorite,Order
from .serializers import ProductSerializer, FavoriteSerializer,OrderSerializer
import uuid
from datetime import datetime
from django.utils import timezone
class ProductListCreate(generics.ListCreateAPIView):
    """商品列表与发布"""
    queryset = Product.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]  # GET游客可看，POST需登录
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("请先登录")
        product = serializer.save(seller=self.request.user)

        # 处理多图上传
        images_data = self.request.FILES.getlist('images')
        for image in images_data:
            ProductImage.objects.create(product=product, image=image)


class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    """商品详情"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class MyProductsView(APIView):
    """我的发布"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(seller=request.user).order_by('-created_at')
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class FavoriteListView(APIView):
    """我的收藏列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = Favorite.objects.filter(user=request.user).order_by('-created_at')
        serializer = FavoriteSerializer(favorites, many=True, context={'request': request})
        return Response(serializer.data)


class FavoriteCreateDestroyView(APIView):
    """收藏/取消收藏"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"detail": "缺少product_id"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)

        if Favorite.objects.filter(user=request.user, product=product).exists():
            return Response({"detail": "已收藏"}, status=status.HTTP_400_BAD_REQUEST)

        favorite = Favorite.objects.create(user=request.user, product=product)
        serializer = FavoriteSerializer(favorite, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"detail": "缺少product_id"}, status=status.HTTP_400_BAD_REQUEST)

        favorite = Favorite.objects.filter(user=request.user, product_id=product_id)
        if not favorite.exists():
            return Response({"detail": "未收藏"}, status=status.HTTP_404_NOT_FOUND)

        favorite.delete()
        return Response({"detail": "已取消收藏"}, status=status.HTTP_204_NO_CONTENT)


class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"detail": "缺少product_id"}, status=400)

        product = get_object_or_404(Product, id=product_id)

        # 不能买自己的商品
        if product.seller == request.user:
            return Response({"detail": "不能购买自己的商品"}, status=400)

        # 创建订单
        order = Order.objects.create(
            buyer=request.user,
            seller=product.seller,
            product=product,
            price=product.price,
            status='pending'
        )

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=201)
class WeChatPayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({"detail": "缺少order_id"}, status=400)

        order = get_object_or_404(Order, id=order_id, buyer=request.user, status='pending')

        # 这里假设你已配置微信支付参数（settings.py 或单独文件）
        # 实际开发需接入微信支付SDK（微信支付商户号、appid、secret、key等）
        # 以下是简化示例（真实项目需用微信支付官方SDK）

        # 模拟生成预支付参数（实际替换为微信支付统一下单接口）
        prepay_data = {
            "appId": "your_appid",
            "timeStamp": str(int(datetime.now().timestamp())),
            "nonceStr": str(uuid.uuid4()),
            "package": f"prepay_id=wx20260122130100000000000000000000",
            "signType": "MD5",
            "paySign": "模拟签名"  # 实际用MD5签名
        }

        # 标记订单为已支付（测试用，实际在支付回调中更新）
        order.status = 'paid'
        order.paid_at = timezone.now()
        order.transaction_id = "模拟交易号"
        order.save()

        return Response({
            "code": 0,
            "msg": "支付参数生成成功",
            "data": prepay_data
        })



