# store/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField("分类名称", max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    title = models.CharField("标题", max_length=200)
    description = models.TextField("描述", blank=True)
    price = models.DecimalField("价格", max_digits=12, decimal_places=2)
    machinery_type = models.CharField("设备类型", max_length=50, blank=True)
    brand = models.CharField("品牌", max_length=100, blank=True)
    model_number = models.CharField("型号", max_length=100, blank=True)
    manufacture_year = models.IntegerField("出厂年份", null=True, blank=True)
    working_hours = models.IntegerField("工作小时", null=True, blank=True)
    location_province = models.CharField("省份", max_length=50, blank=True)
    location_city = models.CharField("城市", max_length=50, blank=True)
    condition_level = models.CharField("成色", max_length=10, blank=True)
    contact_type = models.CharField("联系方式类型", max_length=20, choices=[('phone', '手机号'), ('wechat', '微信号')], blank=True, null=True)
    contact_value = models.CharField("联系方式值", max_length=100, blank=True, null=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField("是否上架", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField("图片", upload_to='products/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.title}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} favorites {self.product}"

class Order(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_bought')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_sold')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[('pending', '待支付'), ('paid', '已支付'), ('shipped', '已发货'), ('completed', '已完成'), ('cancelled', '已取消')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    tracking_number = models.CharField("物流单号", max_length=100, blank=True, null=True)
    shipping_company = models.CharField("物流公司", max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} by {self.buyer}"