# store/urls.py
from django.urls import path
from .views import (
    ProductListCreate, ProductDetail, MyProductsView,
    FavoriteListView, FavoriteCreateDestroyView,
    MyOrdersView, SellerOrdersView, OrderCreateView, OrderUpdateView,SimulatePayView,ProductSearchView
)

urlpatterns = [
    path('products/', ProductListCreate.as_view()),
    path('products/<int:pk>/', ProductDetail.as_view()),
    path('my-products/', MyProductsView.as_view()),
    path('favorites/', FavoriteListView.as_view()),
    path('favorite/', FavoriteCreateDestroyView.as_view()),
    # 新增订单路由
    path('orders/', OrderCreateView.as_view()),
    path('orders/<int:pk>/', OrderUpdateView.as_view()),
    path('orders/my/', MyOrdersView.as_view()),
    path('orders/seller/', SellerOrdersView.as_view()),
path('orders/simulate-pay/', SimulatePayView.as_view(), name='simulate-pay'),
path('products/search/', ProductSearchView.as_view(), name='product-search'),
]