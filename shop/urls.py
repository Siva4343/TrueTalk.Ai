from django.urls import path
from .views import (
    CategoryList, ProductList, AddToCart, GetCart,
    CreateOrder, ListOrders
)

urlpatterns = [
    path("categories/", CategoryList.as_view()),
    path("products/", ProductList.as_view()),

    path("cart/", GetCart.as_view()),
    path("cart/add/<int:product_id>/", AddToCart.as_view()),

    path("order/create/", CreateOrder.as_view()),
    path("orders/", ListOrders.as_view()),
]
