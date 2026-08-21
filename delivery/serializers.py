from decimal import Decimal, ROUND_CEILING

from django.db import transaction
from rest_framework import serializers

from .models import DeliveryOrder, DeliveryOrderItem


class DeliveryOrderItemSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)
    product_name = serializers.CharField(source='product.name', read_only=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = DeliveryOrderItem
        fields = ['product', 'product_name', 'quantity', 'price', 'subtotal', 'notes']

    def validate_product(self, product):
        if not product.is_available:
            raise serializers.ValidationError('Bu mahsulot hozir mavjud emas.')
        return product


class DeliveryOrderSerializer(serializers.ModelSerializer):
    distance_km = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=Decimal('0.00'),
        required=True,
    )
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    items = DeliveryOrderItemSerializer(many=True, required=True, allow_empty=False)

    class Meta:
        model = DeliveryOrder
        fields = [
            'id', 'customer', 'customer_name', 'customer_phone', 'created_by', 'created_by_name',
            'courier_name', 'courier_phone', 'delivery_address', 'latitude', 'longitude', 'distance_km', 'status',
            'subtotal', 'delivery_fee', 'discount', 'total_price', 'payment_type', 'paid_amount',
            'debt_amount', 'is_paid', 'notes', 'created_at', 'closed_at',
            'cancelled_at', 'cancel_reason', 'items',
        ]
        read_only_fields = [
            'id', 'created_by', 'status', 'subtotal', 'delivery_fee', 'total_price', 'payment_type', 'paid_amount',
            'debt_amount', 'is_paid', 'created_at', 'closed_at',
            'cancelled_at', 'cancel_reason',
        ]

    def get_created_by_name(self, order):
        return order.created_by.get_full_name() or order.created_by.phone

    def validate(self, attrs):
        distance_km = attrs.get('distance_km', getattr(self.instance, 'distance_km', Decimal('0.00')))
        extra_distance = max(distance_km - Decimal('1.00'), Decimal('0.00'))
        delivery_fee = extra_distance.to_integral_value(rounding=ROUND_CEILING) * Decimal('5000.00')
        discount = attrs.get('discount', getattr(self.instance, 'discount', Decimal('0.00')))
        if discount < 0:
            raise serializers.ValidationError({'discount': 'discount manfiy bo‘la olmaydi.'})
        if self.instance and discount > self.instance.subtotal + delivery_fee:
            raise serializers.ValidationError({'discount': 'Chegirma umumiy summadan katta bo‘la olmaydi.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = DeliveryOrder.objects.create(**validated_data)
        subtotal = Decimal('0.00')
        for item_data in items_data:
            product = item_data['product']
            item = DeliveryOrderItem.objects.create(
                delivery_order=order,
                product=product,
                quantity=item_data['quantity'],
                price=product.price,
                notes=item_data.get('notes', ''),
            )
            subtotal += item.subtotal
        if order.discount > subtotal + order.delivery_fee:
            raise serializers.ValidationError({'discount': 'Chegirma umumiy summadan katta bo‘la olmaydi.'})
        order.subtotal = subtotal
        order.save(update_fields=['subtotal'])
        return order

    def update(self, instance, validated_data):
        if 'items' in validated_data:
            raise serializers.ValidationError('Mahsulotlar ro‘yxatini o‘zgartirib bo‘lmaydi.')
        return super().update(instance, validated_data)
