from django.contrib import admin

from .models import DeliveryOrder, DeliveryOrderItem


class DeliveryOrderItemInline(admin.TabularInline):
    model = DeliveryOrderItem
    extra = 0
    readonly_fields = ('price', 'subtotal')


@admin.register(DeliveryOrder)
class DeliveryOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'courier_name', 'courier_phone', 'distance_km', 'delivery_fee', 'status', 'total_price', 'payment_type', 'is_paid', 'created_at')
    list_filter = ('status', 'payment_type', 'is_paid', 'created_at')
    search_fields = ('customer__full_name', 'customer__phone', 'courier_name', 'courier_phone')
    readonly_fields = ('subtotal', 'delivery_fee', 'total_price', 'paid_amount', 'debt_amount', 'is_paid', 'created_at')
    inlines = [DeliveryOrderItemInline]


@admin.register(DeliveryOrderItem)
class DeliveryOrderItemAdmin(admin.ModelAdmin):
    list_display = ('delivery_order', 'product', 'quantity', 'price', 'subtotal')
