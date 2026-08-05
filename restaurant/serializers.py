from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import (
    Category,
    Customer,
    Order,
    OrderItem,
    Product,
    RestaurantTable,
    User,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'full_name', 'phone', 'address', 'created_at']
        read_only_fields = ['id', 'created_at']


class WaiterSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'phone', 'full_name']

    def get_full_name(self, waiter):
        return waiter.get_full_name() or waiter.phone


class RestaurantTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantTable
        fields = ['id', 'number', 'capacity', 'is_active']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category', 'category_name', 'is_available']


class OrderItemSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)
    product_name = serializers.CharField(source='product.name', read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'quantity', 'price', 'subtotal']

    def validate_product(self, product):
        if not product.is_available:
            raise serializers.ValidationError('Bu mahsulot hozir mavjud emas.')
        return product


class OrderSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(
        choices=[
            choice
            for choice in Order.STATUS_CHOICES
            if choice[0] != 'closed'
        ],
        required=False,
    )
    waiter = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='afitsant', is_active=True),
        required=True,
        allow_null=False,
        error_messages={
            'does_not_exist': 'Bunday faol afitsant topilmadi.',
            'incorrect_type': 'waiter maydoniga afitsant ID sini kiriting.',
        },
    )
    table = serializers.PrimaryKeyRelatedField(
        queryset=RestaurantTable.objects.filter(is_active=True),
        required=True,
        allow_null=False,
        error_messages={
            'does_not_exist': 'Bunday faol stol topilmadi.',
            'incorrect_type': 'table maydoniga stol ID sini kiriting.',
        },
    )
    waiter_name = serializers.SerializerMethodField()
    table_number = serializers.IntegerField(source='table.number', read_only=True)
    items = OrderItemSerializer(many=True, required=True, allow_empty=False)

    class Meta:
        model = Order
        fields = [
            'id',
            'customer',
            'waiter',
            'waiter_name',
            'table',
            'table_number',
            'status',
            'total_price',
            'paid_amount',
            'debt_amount',
            'payment_type',
            'is_paid',
            'notes',
            'created_at',
            'closed_at',
            'items',
        ]
        read_only_fields = [
            'id', 'total_price', 'paid_amount', 'debt_amount', 'payment_type',
            'is_paid', 'created_at', 'closed_at',
        ]

    def get_waiter_name(self, order):
        if not order.waiter_id:
            return None
        return order.waiter.get_full_name() or order.waiter.phone

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        total_price = Decimal('0.00')

        for item_data in items_data:
            product = item_data['product']
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                price=product.price,
            )
            total_price += order_item.subtotal
        order.total_price = total_price
        order.save(update_fields=['total_price'])
        return order

    def update(self, instance, validated_data):
        if instance.status == 'closed':
            raise serializers.ValidationError(
                'Yopilgan buyurtmani o‘zgartirib bo‘lmaydi.'
            )
        return super().update(instance, validated_data)
