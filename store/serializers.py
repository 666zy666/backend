# store/serializers.py
from rest_framework import serializers
from .models import Category, Product, ProductImage, Favorite, Order,Banner

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'price', 'machinery_type', 'brand', 'model_number', 'manufacture_year', 'working_hours', 'location_province', 'location_city', 'condition_level', 'contact_type', 'contact_value', 'seller_username', 'category_name', 'images', 'is_active', 'created_at', 'updated_at']

class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'product', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_image = serializers.SerializerMethodField(read_only=True)
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    buyer_username = serializers.CharField(source='buyer.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    def get_product_image(self, obj):
        request = self.context.get('request')
        if obj.product.images.exists() and request:
            return request.build_absolute_uri(obj.product.images.first().image.url)
        return None

    class Meta:
        model = Order
        fields = ['id', 'buyer', 'buyer_username', 'seller', 'seller_username', 'product', 'product_title', 'product_image', 'price', 'status', 'status_display', 'created_at', 'paid_at', 'shipped_at', 'completed_at', 'tracking_number', 'shipping_company']
        read_only_fields = ['buyer', 'seller', 'product', 'price', 'status', 'status_display', 'created_at', 'paid_at', 'shipped_at', 'completed_at']

class BannerSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    class Meta:
        model = Banner
        fields = ['id', 'title', 'image', 'link', 'order']

