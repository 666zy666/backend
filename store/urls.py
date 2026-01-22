from django.urls import path
from .views import ProductListCreate, ProductDetail,MyProductsView,FavoriteListView,FavoriteCreateDestroyView,OrderCreateView,WeChatPayView

urlpatterns = [
    path('products/', ProductListCreate.as_view()),
    path('products/<int:pk>/', ProductDetail.as_view()),
    path('my-products/', MyProductsView.as_view(), name='my-products'),
    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),
    path('favorite/', FavoriteCreateDestroyView.as_view(), name='favorite-create-destroy'),
path('orders/', OrderCreateView.as_view(), name='order-create'),
    path('orders/pay/', WeChatPayView.as_view(), name='order-pay'),
]