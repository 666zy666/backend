# account/admin_urls.py  — Admin management API routes
# All routes are mounted at /api/admin/ in backend/urls.py
from django.urls import path
from .admin_views import (
    AdminAuthLoginView,
    AdminAuthMeView,
    AdminDashboardOverviewView,
    AdminDashboardTrendView,
    AdminUserListView,
    AdminUserDetailView,
    AdminProductListView,
    AdminProductDetailView,
    AdminOrderListView,
    AdminOrderDetailView,
    AdminOrderStatusView,
    AdminBannerListView,
    AdminBannerDetailView,
)

urlpatterns = [
    # Auth
    path('auth/login/', AdminAuthLoginView.as_view(), name='admin-auth-login'),
    path('auth/me/', AdminAuthMeView.as_view(), name='admin-auth-me'),

    # Dashboard
    path('dashboard/overview/', AdminDashboardOverviewView.as_view(), name='admin-dashboard-overview'),
    path('dashboard/trend/', AdminDashboardTrendView.as_view(), name='admin-dashboard-trend'),

    # Users
    path('users/', AdminUserListView.as_view(), name='admin-users'),
    path('users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),

    # Products
    path('products/', AdminProductListView.as_view(), name='admin-products'),
    path('products/<int:pk>/', AdminProductDetailView.as_view(), name='admin-product-detail'),

    # Orders
    path('orders/', AdminOrderListView.as_view(), name='admin-orders'),
    path('orders/<int:pk>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('orders/<int:pk>/status/', AdminOrderStatusView.as_view(), name='admin-order-status'),

    # Banners
    path('banners/', AdminBannerListView.as_view(), name='admin-banners'),
    path('banners/<int:pk>/', AdminBannerDetailView.as_view(), name='admin-banner-detail'),
]
