from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Product
from .serializers import ProductSerializer


class SellerProducts(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(seller=request.user)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        data['seller'] = request.user.id  # attach seller
        serializer = ProductSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Product added successfully"}, status=201)

        return Response(serializer.errors, status=400)


class SellerProductDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        product = Product.objects.get(id=pk, seller=request.user)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk):
        product = Product.objects.get(id=pk, seller=request.user)
        serializer = ProductSerializer(product, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Product updated successfully"})

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        product = Product.objects.get(id=pk, seller=request.user)
        product.delete()
        return Response({"message": "Product deleted"})
