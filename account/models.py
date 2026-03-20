from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=11, blank=True)
    avatar = models.URLField(blank=True)
    wechat_openid = models.CharField(max_length=64, unique=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    recipient_name = models.CharField('收件人', max_length=50)
    phone = models.CharField('联系电话', max_length=20)
    province = models.CharField('省份', max_length=50, blank=True)
    city = models.CharField('城市', max_length=50, blank=True)
    district = models.CharField('区县', max_length=50, blank=True)
    detail = models.CharField('详细地址', max_length=200)
    is_default = models.BooleanField('是否默认', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = '收货地址'
        verbose_name_plural = '收货地址'

    def __str__(self):
        return f"{self.recipient_name} - {self.detail}"