from rest_framework import serializers
from .models import Product, Cart, Order


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class CartSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'product', 'product_details', 'quantity', 'added_at']


class OrderSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'product',
            'product_details',
            'quantity',
            'total_price',
            'status',
            'ordered_at',
        ]
