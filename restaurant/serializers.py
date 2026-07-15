from decimal import Decimal
from rest_framework import serializers
from .models import Category, Customer, Order, OrderItem, Product
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'full_name', 'phone', 'address', 'created_at']
        read_only_fields = ['id', 'created_at']
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category', 'category_name', 'is_available']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'quantity', 'price', 'subtotal']
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)

    class Meta:
        model = Order
        fields = [
            'id',
            'customer',
            'waiter',
            'table',
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
            'id', 'total_price', 'paid_amount', 'debt_amount', 'is_paid',
            'created_at', 'closed_at',
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
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
