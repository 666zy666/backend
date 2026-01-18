# store/views.py - 完整版（2025年最新，支持游客查看商品列表、登录发布、我的发布、图片完整URL、收藏接口等）

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Product, ProductImage, Category, Favorite
from .serializers import ProductSerializer, ProductImageSerializer, CategorySerializer, FavoriteSerializer


# 商品列表与创建（游客可看列表，登录可发布）
class ProductListCreate(generics.ListCreateAPIView):
    queryset = Product.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]  # 列表允许游客，创建需登录
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_context(self):
        """关键：传 request 上下文，确保图片返回完整 URL"""
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_create(self, serializer):
        """发布时强制设置当前用户为卖家"""
        if not self.request.user.is_authenticated:
            raise PermissionDenied("请先登录")
        product = serializer.save(seller=self.request.user)

        # 处理多图上传
        images_data = self.request.FILES.getlist('images')
        for image in images_data:
            ProductImage.objects.create(product=product, image=image)

        # 自动设置默认分类（防止 category 必填报错）
        if not product.category:
            default_cat, _ = Category.objects.get_or_create(name='其他机械')
            product.category = default_cat
            product.save()


# 商品详情（游客可看）
class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]  # 详情允许游客

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_update(self, serializer):
        """更新时校验权限（可选：只允许卖家修改）"""
        if self.request.user != serializer.instance.seller:
            raise PermissionDenied("只能修改自己的商品")
        serializer.save()


# 我的发布（仅登录用户）
class MyProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(seller=request.user).order_by('-created_at')
        serializer = ProductSerializer(
            products,
            many=True,
            context={'request': request}  # 确保图片 URL 完整
        )
        return Response(serializer.data)


# 收藏列表（我的收藏）
class FavoriteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = Favorite.objects.filter(user=request.user).order_by('-created_at')
        serializer = FavoriteSerializer(
            favorites,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


# 收藏/取消收藏单个商品
class FavoriteCreateDestroyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"detail": "缺少 product_id"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)

        # 检查是否已收藏
        if Favorite.objects.filter(user=request.user, product=product).exists():
            return Response({"detail": "已收藏"}, status=status.HTTP_400_BAD_REQUEST)

        favorite = Favorite.objects.create(user=request.user, product=product)
        serializer = FavoriteSerializer(favorite, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"detail": "缺少 product_id"}, status=status.HTTP_400_BAD_REQUEST)

        favorite = Favorite.objects.filter(user=request.user, product_id=product_id)
        if not favorite.exists():
            return Response({"detail": "未收藏"}, status=status.HTTP_404_NOT_FOUND)

        favorite.delete()
        return Response({"detail": "已取消收藏"}, status=status.HTTP_204_NO_CONTENT)