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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # 防止重复收藏
        verbose_name = "收藏"
        verbose_name_plural = "收藏"

    def __str__(self):
        return f"{self.user} 收藏了 {self.product.title}"

class Order(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_bought')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_sold')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    STATUS_PENDING_PAYMENT = 'pending_payment'
    STATUS_PENDING_RECEIPT = 'pending_receipt'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, '待付款'),
        (STATUS_PENDING_RECEIPT, '待收货'),
        (STATUS_COMPLETED, '已完成'),
        (STATUS_CANCELLED, '已取消'),
        # 兼容旧数据保留
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('shipped', '已发货'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING_PAYMENT
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

class Banner(models.Model):
    title = models.CharField(max_length=100, blank=True, verbose_name="标题")
    image = models.ImageField(upload_to='banners/%Y/%m/%d/', verbose_name="轮播图")
    link = models.CharField(max_length=255, blank=True, null=True, verbose_name="跳转链接")
    order = models.PositiveIntegerField(default=0, verbose_name="排序（越小越靠前）")
    is_active = models.BooleanField(default=True, verbose_name="是否显示")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = "轮播图"
        verbose_name_plural = "轮播图"

    def __str__(self):
        return self.title or f"Banner {self.id}"