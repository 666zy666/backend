# account/urls.py
from django.urls import path
from .views import PasswordLoginView, RegisterView,WeChatLoginView

urlpatterns = [
    path('login/', PasswordLoginView.as_view()),
    path('register/', RegisterView.as_view()),  # 新增这行
    path('wx-login/', WeChatLoginView.as_view()),
]