from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .models import Product
from .serializers import ProductSerializer


class SellerProducts(APIView):
    permission_classes = []          # fetch does NOT send CSRF
    authentication_classes = []      # disable session CSRF

    def get(self, request):
        """Return all products"""
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=200)

    def post(self, request):
        """
        Add a new product
        Compatible with:
        - fetch() + FormData
        - fetch() + JSON
        """

        data = request.data.copy()   # handles json + multipart
        files = request.FILES

        # Handle features from fetch
        features_raw = data.get("features", "[]")
        data["features"] = features_raw

        # Temporary seller assignment (fix later with JWT)
        seller = User.objects.first()
        if not seller:
            return Response({"error": "No seller available"}, status=400)

        data["seller"] = seller.id

        serializer = ProductSerializer(data=data)

        if serializer.is_valid():
            serializer.save(image=files.get("image"))
            return Response(
                {"message": "Product added successfully"},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=400)


class SellerProductDetail(APIView):
    permission_classes = []
    authentication_classes = []

    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=404)

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=200)

    def put(self, request, pk):
        """
        Update product
        Works with both:
        - fetch + JSON
        - fetch + FormData
        """
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=404)

        data = request.data.copy()
        files = request.FILES

        features_raw = data.get("features", "[]")
        data["features"] = features_raw

        serializer = ProductSerializer(product, data=data, partial=True)

        if serializer.is_valid():
            serializer.save(image=files.get("image"))
            return Response({"message": "Product updated successfully"}, status=200)

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=404)

        product.delete()
        return Response({"message": "Product deleted"}, status=200)
