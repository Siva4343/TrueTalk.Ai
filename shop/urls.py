from django.urls import path
from .views import SellerProducts, SellerProductDetail

urlpatterns = [
    path("products/", SellerProducts.as_view()),
    path("products/<int:pk>/", SellerProductDetail.as_view()),
]