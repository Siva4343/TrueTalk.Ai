from django.urls import path
from .views import (
    SellerProducts,
    SellerProductDetail,
    CartView,
    OrderView,
)

urlpatterns = [

    # PRODUCTS (Seller + Buyer view)
    path("products/", SellerProducts.as_view()),          # GET = list products
    path("products/<int:pk>/", SellerProductDetail.as_view()),

    # BUYER CART
    path("cart/", CartView.as_view()),                   # GET, POST, DELETE

    # BUYER ORDERS
    path("orders/", OrderView.as_view()),                # GET, POST
]
