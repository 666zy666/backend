from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=11, blank=True)
    avatar = models.URLField(blank=True)
    wechat_openid = models.CharField(max_length=64, unique=True, blank=True)
    is_verified = models.BooleanField(default=False)