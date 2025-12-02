from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Cart, Order
from .serializers import (
    ProductSerializer,
    CartSerializer,
    OrderSerializer,
)

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404


# ---------------------------------------------------
# SELLER PRODUCT VIEWS
# ---------------------------------------------------

class SellerProducts(APIView):
    permission_classes = []  # You can later add permissions

    def get(self, request):
        """List all products (seller + buyer can see)"""
        products = Product.objects.all()
        return Response(ProductSerializer(products, many=True).data)

    def post(self, request):
        """Seller adds a product"""
        data = request.data.copy()

        # Safely handle features
        data["features"] = data.get("features", "[]")

        # Default seller until auth added
        seller = User.objects.first()
        if not seller:
            return Response({"error": "No users in database!"}, status=400)

        data["seller"] = seller.id

        serializer = ProductSerializer(data=data)
        if serializer.is_valid():
            serializer.save(image=request.FILES.get("image"))
            return Response(
                {"message": "Product added successfully"},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SellerProductDetail(APIView):
    permission_classes = []

    def get(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        return Response(ProductSerializer(product).data)

    def put(self, request, pk):
        product = get_object_or_404(Product, id=pk)

        data = request.data.copy()
        data["features"] = data.get("features", "[]")

        serializer = ProductSerializer(product, data=data, partial=True)

        if serializer.is_valid():
            serializer.save(image=request.FILES.get("image"))
            return Response({"message": "Product updated successfully"})

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        product.delete()
        return Response({"message": "Product deleted"})


# ---------------------------------------------------
# BUYER CART VIEWS
# ---------------------------------------------------

class CartView(APIView):
    permission_classes = []

    def get(self, request):
        """Buyer sees cart items"""
        items = Cart.objects.all()
        return Response(CartSerializer(items, many=True).data)

    def post(self, request):
        """Add item to cart"""
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Added to cart"}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=400)

    def delete(self, request):
        """Clear cart"""
        Cart.objects.all().delete()
        return Response({"message": "Cart cleared"})


# ---------------------------------------------------
# BUYER ORDER VIEWS
# ---------------------------------------------------

class OrderView(APIView):
    permission_classes = []

    def get(self, request):
        """Buyer gets order history"""
        orders = Order.objects.all()
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request):
        """Place an order"""
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Order placed successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=400)
