# store/urls.py
from django.urls import path
from .views import (
    ProductListCreate, ProductDetail, MyProductsView,
    FavoriteListView,
    MyOrdersView, SellerOrdersView, OrderCreateView, OrderUpdateView, SimulatePayView, ProductSearchView,
    BannerListView, FavoriteCreateView, FavoriteDeleteView
)

urlpatterns = [
    path('products/', ProductListCreate.as_view()),
    path('products/<int:pk>/', ProductDetail.as_view()),
    path('my-products/', MyProductsView.as_view()),
    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),
    path('favorites/add/', FavoriteCreateView.as_view(), name='favorite-add'),
    path('favorites/remove/<int:product_id>/', FavoriteDeleteView.as_view(), name='favorite-remove'),
    # 新增订单路由
    path('orders/', OrderCreateView.as_view()),
    path('orders/<int:pk>/', OrderUpdateView.as_view()),
    path('orders/my/', MyOrdersView.as_view()),
    path('orders/seller/', SellerOrdersView.as_view()),
path('orders/simulate-pay/', SimulatePayView.as_view(), name='simulate-pay'),
path('products/search/', ProductSearchView.as_view(), name='product-search'),
path('banners/', BannerListView.as_view(), name='banner-list'),
]