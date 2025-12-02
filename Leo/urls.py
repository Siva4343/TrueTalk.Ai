from django.urls import path
from .views import ProductCreateView, ProductListView, ProductDetailView

urlpatterns = [
    path("products/add/", ProductCreateView.as_view(), name="product-add"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
]