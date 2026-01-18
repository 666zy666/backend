# store/serializers.py - 完整防崩版
from rest_framework import serializers
from .models import Product, ProductImage, Category,Favorite


class ProductImageSerializer(serializers.ModelSerializer):
    """
    商品图片序列化器 - 返回完整 URL，防 request 为 None
    """
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request is not None:
            url = request.build_absolute_uri(obj.image.url)
            # 上线时可强制 HTTPS
            # url = url.replace('http://', 'https://')
            return url
        # 兜底：返回空或默认图 URL
        return None

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'uploaded_at']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    """
    商品主序列化器 - 列表/详情通用
    """
    images = ProductImageSerializer(many=True, read_only=True)
    seller_username = serializers.CharField(source='seller.username', read_only=True, allow_null=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price',
            'machinery_type', 'brand', 'model_number',
            'manufacture_year', 'working_hours',
            'location_province', 'location_city',
            'condition_level', 'is_active',
            'created_at', 'updated_at',
            'seller_username', 'category_name',
            'images'
        ]
        read_only_fields = ['created_at', 'updated_at', 'seller_username', 'is_active']


# 我的发布专用（可选，字段更少）
class MyProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'price', 'is_active', 'created_at', 'images']
# store/serializers.py - 收藏序列化器
class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)  # 返回完整商品信息

    class Meta:
        model = Favorite
        fields = ['id', 'product', 'created_at']
        read_only_fields = ['created_at']