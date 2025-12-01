from django.urls import path
from .views import SellerProducts, SellerProductDetail

urlpatterns = [
    path("products/", SellerProducts.as_view()),           # GET list, POST add
    path("products/<int:pk>/", SellerProductDetail.as_view()),   # GET, PUT, DELETE
]
