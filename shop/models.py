from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('draft', 'Draft'),
    )

    seller = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    description = models.TextField()
    features = models.JSONField(default=list)
    stock = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------
# BUYER CART
# ---------------------------------------------------
class Cart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart: {self.product.name} x {self.quantity}"


# ---------------------------------------------------
# BUYER ORDERS
# ---------------------------------------------------
class Order(models.Model):
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS, default='pending'
    )
    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order: {self.product.name} ({self.status})"
