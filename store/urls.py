# store/urls.py
from django.urls import path
from .views import (
    ProductListCreate, ProductDetail, MyProductsView,
    FavoriteListView, FavoriteCreateView, FavoriteDeleteView,
    MyOrdersView, SellerOrdersView, OrderCreateView, OrderUpdateView,
    SimulatePayView, OrderPayView, OrderCancelView, OrderConfirmView,
    ProductSearchView, BannerListView,
)

urlpatterns = [
    path('products/', ProductListCreate.as_view()),
    path('products/search/', ProductSearchView.as_view(), name='product-search'),
    path('products/<int:pk>/', ProductDetail.as_view()),
    path('my-products/', MyProductsView.as_view()),
    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),
    path('favorites/add/', FavoriteCreateView.as_view(), name='favorite-add'),
    path('favorites/remove/<int:product_id>/', FavoriteDeleteView.as_view(), name='favorite-remove'),
    path('banners/', BannerListView.as_view(), name='banner-list'),
    # 订单
    path('orders/', OrderCreateView.as_view()),
    path('orders/my/', MyOrdersView.as_view()),
    path('orders/seller/', SellerOrdersView.as_view()),
    path('orders/simulate-pay/', SimulatePayView.as_view(), name='simulate-pay'),
    path('orders/<int:pk>/', OrderUpdateView.as_view()),
    path('orders/<int:pk>/pay/', OrderPayView.as_view(), name='order-pay'),
    path('orders/<int:pk>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('orders/<int:pk>/confirm/', OrderConfirmView.as_view(), name='order-confirm'),
]
