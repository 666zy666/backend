# account/urls.py
from django.urls import path
from .views import (
    PasswordLoginView, RegisterView, WeChatLoginView,
    UserProfileView, ChangePasswordView,
    AddressListCreateView, AddressDetailView, SetDefaultAddressView,
    AdminStatsView, AdminUserListView, AdminProductListView, AdminOrderListView,
)

urlpatterns = [
    path('login/', PasswordLoginView.as_view()),
    path('register/', RegisterView.as_view()),
    path('wx-login/', WeChatLoginView.as_view()),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # 收货地址
    path('addresses/', AddressListCreateView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),
    path('addresses/<int:pk>/set-default/', SetDefaultAddressView.as_view(), name='address-set-default'),

    # 管理员接口
    path('admin/stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/products/', AdminProductListView.as_view(), name='admin-products'),
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-orders'),
]
