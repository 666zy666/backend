# store/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    """设备分类"""
    name = models.CharField("分类名称", max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "分类"
        verbose_name_plural = "分类"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """二手机械设备"""
    title = models.CharField("标题", max_length=200)
    description = models.TextField("详细描述", blank=True)
    price = models.DecimalField("价格(元)", max_digits=12, decimal_places=2)
    machinery_type = models.CharField("设备类型", max_length=50, blank=True)
    brand = models.CharField("品牌", max_length=100, blank=True)
    model_number = models.CharField("型号", max_length=100, blank=True)
    manufacture_year = models.IntegerField("出厂年份", null=True, blank=True)
    working_hours = models.IntegerField("工作小时", null=True, blank=True)
    location_province = models.CharField("所在省份", max_length=50, blank=True)
    location_city = models.CharField("所在城市", max_length=50, blank=True)
    condition_level = models.CharField("成色", max_length=10, blank=True)

    # 联系方式
    contact_type = models.CharField(
        "联系方式类型",
        max_length=20,
        choices=[('phone', '手机号'), ('wechat', '微信号')],
        blank=True,
        null=True
    )
    contact_value = models.CharField("联系方式值", max_length=100, blank=True, null=True)

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products_sold', verbose_name="卖家")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')

    # 状态与时间
    is_active = models.BooleanField("是否上架", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "设备"
        verbose_name_plural = "设备"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    """商品图片"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField("图片", upload_to='products/%Y/%m/%d/')
    uploaded_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        verbose_name = "商品图片"
        verbose_name_plural = "商品图片"
        ordering = ['uploaded_at']

    def __str__(self):
        return f"{self.product.title} 的图片"


class Favorite(models.Model):
    """用户收藏"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField("收藏时间", auto_now_add=True)

    class Meta:
        verbose_name = "收藏"
        verbose_name_plural = "收藏"
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} 收藏了 {self.product.title}"

# store/models.py - 添加到文件末尾
class Order(models.Model):
    """订单"""
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_bought', verbose_name="买家")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_sold', verbose_name="卖家")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    price = models.DecimalField("订单金额", max_digits=12, decimal_places=2)
    status = models.CharField(
        "订单状态",
        max_length=20,
        choices=[
            ('pending', '待支付'),
            ('paid', '已支付'),
            ('shipped', '已发货'),
            ('completed', '已完成'),
            ('cancelled', '已取消')
        ],
        default='pending'
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    paid_at = models.DateTimeField("支付时间", null=True, blank=True)
    transaction_id = models.CharField("微信支付订单号", max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "订单"
        verbose_name_plural = "订单"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.buyer.username} 购买 {self.product.title}"