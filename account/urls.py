# account/urls.py
from django.urls import path
from .views import (
    PasswordLoginView, RegisterView, WeChatLoginView,
    UserProfileView, ChangePasswordView,
    AddressListCreateView, AddressDetailView, SetDefaultAddressView,
    AdminStatsView, AdminUserListView, AdminUserDetailView,
    AdminProductListView, AdminProductDetailView, AdminProductStatusView,
    AdminOrderListView, AdminOrderDetailView,
    AdminLoginView, AdminMeView,
    AvatarUploadView,
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
    path('avatar/', AvatarUploadView.as_view()),

    # 管理员认证
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('admin/me/', AdminMeView.as_view(), name='admin-me'),

    # 管理员统计面板
    path('admin/stats/', AdminStatsView.as_view(), name='admin-stats'),

    # 管理员用户管理
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),

    # 管理员商品管理
    path('admin/products/', AdminProductListView.as_view(), name='admin-products'),
    path('admin/products/<int:pk>/', AdminProductDetailView.as_view(), name='admin-product-detail'),
    path('admin/products/<int:pk>/status/', AdminProductStatusView.as_view(), name='admin-product-status'),

    # 管理员订单管理
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-orders'),
    path('admin/orders/<int:pk>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),
]
