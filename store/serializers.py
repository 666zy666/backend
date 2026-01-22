# store/serializers.py
from rest_framework import serializers
from .models import Product, ProductImage, Category, Favorite,Order


class ProductImageSerializer(serializers.ModelSerializer):
    """商品图片序列化器 - 返回完整URL"""
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request is not None:
            url = request.build_absolute_uri(obj.image.url)
            return url # 可选：强制HTTPS
        return None

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'uploaded_at']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent']


class ProductSerializer(serializers.ModelSerializer):
    """商品主序列化器"""
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
            'contact_type', 'contact_value',
            'created_at', 'updated_at',
            'seller_username', 'category_name',
            'images'
        ]
        read_only_fields = ['created_at', 'updated_at', 'seller_username', 'is_active']


class FavoriteSerializer(serializers.ModelSerializer):
    """收藏记录序列化器"""
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'product', 'created_at']
        read_only_fields = ['created_at']


# store/serializers.py - 添加
class OrderSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    seller_username = serializers.CharField(source='seller.username', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'product', 'product_title', 'seller', 'seller_username',
            'price', 'status', 'created_at', 'paid_at', 'transaction_id'
        ]
        read_only_fields = ['created_at', 'paid_at', 'transaction_id']