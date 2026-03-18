# account/urls.py
from django.urls import path
from .views import PasswordLoginView, RegisterView, WeChatLoginView, UserProfileView, ChangePasswordView

urlpatterns = [
    path('login/', PasswordLoginView.as_view()),
    path('register/', RegisterView.as_view()),  # 新增这行
    path('wx-login/', WeChatLoginView.as_view()),
path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]