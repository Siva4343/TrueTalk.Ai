from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from .serializers import ProductSerializer
from django.contrib.auth.models import User


class SellerProducts(APIView):
    permission_classes = []

    def get(self, request):
        products = Product.objects.all()
        return Response(ProductSerializer(products, many=True).data)

    def post(self, request):
        data = request.POST.copy()
        files = request.FILES

        # Features as plain string (serializer will parse JSON)
        features_raw = data.get("features", "[]")
        data["features"] = features_raw

        # Default seller
        data["seller"] = User.objects.first().id

        serializer = ProductSerializer(data=data)

        if serializer.is_valid():
            serializer.save(image=files.get("image"))
            return Response({"message": "Product added successfully"}, status=201)

        return Response(serializer.errors, status=400)


class SellerProductDetail(APIView):
    permission_classes = []

    def get(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        return Response(ProductSerializer(product).data)

    def put(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        data = request.POST.copy()
        files = request.FILES

        features_raw = data.get("features", "[]")
        data["features"] = features_raw

        serializer = ProductSerializer(product, data=data, partial=True)

        if serializer.is_valid():
            serializer.save(image=files.get("image"))
            return Response({"message": "Product updated successfully"})

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        product.delete()
        return Response({"message": "Product deleted"})
