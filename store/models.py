# store/models.py - 2025年终极稳定版
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# 设备分类
class Category(models.Model):
    name = models.CharField("分类名称", max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "设备分类"
        verbose_name_plural = "设备分类"

    def __str__(self):
        return self.name


# 设备类型选择（可扩展）
MACHINERY_CHOICES = [
    ('excavator', '挖掘机'),
    ('loader', '装载机'),
    ('bulldozer', '推土机'),
    ('crane', '起重机'),
    ('forklift', '叉车'),
    ('pump_truck', '泵车'),
    ('roller', '压路机'),
    ('grader', '平地机'),
    ('other', '其他机械'),
]

# 成色选择
CONDITION_CHOICES = [
    ('99', '99成新'),
    ('95', '95成新'),
    ('90', '9成新'),
    ('80', '8成新'),
    ('70', '7成新及以下'),
]


# 二手设备主表
class Product(models.Model):
    title = models.CharField("设备标题", max_length=200)
    description = models.TextField("详细描述", blank=True)
    price = models.DecimalField("价格（元）", max_digits=12, decimal_places=2)

    # 分类（允许为空，发布时可写死默认）
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="设备分类"
    )

    # 卖家

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="卖家",
        blank=True,  # 加上这行！
        null=True  # 加上这行！
    )

    # 二手机械核心字段
    machinery_type = models.CharField("设备类型", max_length=20, choices=MACHINERY_CHOICES, default='other')
    brand = models.CharField("品牌", max_length=100, blank=True)
    model_number = models.CharField("型号", max_length=100, blank=True)
    manufacture_year = models.IntegerField("出厂年份", null=True, blank=True)
    working_hours = models.IntegerField("工作小时数", null=True, blank=True)
    location_province = models.CharField("所在省份", max_length=50)
    location_city = models.CharField("所在城市", max_length=50, blank=True)
    condition_level = models.CharField("成色", max_length=10, choices=CONDITION_CHOICES, default='90')

    # 状态控制
    is_active = models.BooleanField("是否上架", default=True)

    # 时间字段
    created_at = models.DateTimeField("发布时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "二手设备"
        verbose_name_plural = "二手设备"

    def __str__(self):
        return f"{self.brand} {self.model_number} - {self.title}"


# 设备图片（支持多图）
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField("设备图片", upload_to='products/%Y/%m/%d/')
    uploaded_at = models.DateTimeField("上传时间", auto_now_add=True)

    def __str__(self):
        return f"{self.product.title} 的图片"


# store/models.py

class Favorite(models.Model):
    """
    用户收藏模型 - 支持用户对商品的收藏
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name="用户"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name="商品"
    )
    created_at = models.DateTimeField("收藏时间", auto_now_add=True)

    class Meta:
        verbose_name = "收藏"
        verbose_name_plural = "收藏"
        unique_together = ('user', 'product')  # 防止重复收藏
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} 收藏了 {self.product.title}"