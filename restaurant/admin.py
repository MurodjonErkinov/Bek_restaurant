from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Category, Customer, Order, OrderItem, Product, RestaurantTable, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'phone', 'role', 'salary', 'is_staff', 'is_active')
    search_fields = ('username', 'phone', 'email')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional info', {'fields': ('role', 'phone', 'salary')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional info', {'fields': ('role', 'phone', 'salary')}),
    )


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'created_at')
    search_fields = ('full_name', 'phone')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name',)


@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ('number', 'capacity', 'is_active')
    list_filter = ('is_active',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'waiter', 'table', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at', 'waiter')
    search_fields = ('customer__full_name',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'subtotal')
