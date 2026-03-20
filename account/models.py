from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=11, blank=True)
    avatar = models.URLField(blank=True, null=True)
    wechat_openid = models.CharField(max_length=64, blank=True, null=True)  # ← 修改这里
    is_verified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user',)   # 保证一对一

    def __str__(self):
        return f"{self.user.username} 的资料"

# 自动创建 UserProfile（第一次登录时自动生成）
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)