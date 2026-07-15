from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('oshpaz', 'Oshpaz'),
        ('kassir', 'Kassir'),
        ('afitsant', 'Afitsant'),
        ('customer', 'Customer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True, null=True)

class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
    )
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.PROTECT)
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
class RestaurantTable(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    capacity = models.PositiveSmallIntegerField(default=4)
    is_active = models.BooleanField(default=True)
class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Yangi'),
        ('cooking', 'Tayyorlanmoqda'),
        ('ready', 'Tayyor'),
        ('closed', 'Yopilgan'),
    ]
    PAYMENT_CHOICES = [
        ('cash', 'Naqd'),
        ('credit', 'Qarz'),
    ]
    customer = models.ForeignKey(Customer, related_name='orders', on_delete=models.CASCADE)
    waiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='waiter_orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'afitsant'},)
    table = models.ForeignKey(
        RestaurantTable,
        related_name='orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    debt_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_type = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    is_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def save(self, *args, **kwargs):
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)


    
