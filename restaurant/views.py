from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from kassa.notifications import send_checkout_notification

from .models import Category, Customer, Order, Product, RestaurantTable, User
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    OrderSerializer,
    ProductSerializer,
    RestaurantTableSerializer,
    WaiterSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_available=True)
    serializer_class = ProductSerializer


class WaiterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(role='afitsant', is_active=True).order_by('id')
    serializer_class = WaiterSerializer


class RestaurantTableViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RestaurantTable.objects.filter(is_active=True).order_by('number')
    serializer_class = RestaurantTableSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = (
        Order.objects
        .select_related('customer', 'waiter', 'table')
        .prefetch_related('items__product')
    )
    serializer_class = OrderSerializer

    @action(detail=True, methods=['post'], url_path='checkout')
    def checkout(self, request, pk=None):
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=pk)
            if order.status == 'closed':
                return Response(
                    {'detail': 'Bu buyurtma avval yopilgan.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not order.waiter_id:
                return Response(
                    {'detail': 'Buyurtmaga afitsant biriktirilmagan.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if order.waiter.role != 'afitsant':
                return Response(
                    {'detail': 'Buyurtmaga biriktirilgan foydalanuvchi afitsant emas.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not order.table_id:
                return Response(
                    {'detail': 'Buyurtmaga stol biriktirilmagan.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payment_type = request.data.get('payment_type', 'cash')
            try:
                paid_amount = Decimal(str(request.data.get('paid_amount', '0')))
            except Exception:
                return Response({'detail': 'paid_amount noto‘g‘ri.'}, status=status.HTTP_400_BAD_REQUEST)

            if payment_type not in dict(Order.PAYMENT_CHOICES):
                return Response({'detail': 'payment_type noto‘g‘ri.'}, status=status.HTTP_400_BAD_REQUEST)
            if paid_amount < 0:
                return Response({'detail': 'paid_amount manfiy bo‘la olmaydi.'}, status=status.HTTP_400_BAD_REQUEST)

            order.payment_type = payment_type
            order.paid_amount = paid_amount
            order.debt_amount = max(order.total_price - paid_amount, Decimal('0.00'))
            order.is_paid = paid_amount >= order.total_price
            order.status = 'closed'
            order.closed_at = timezone.now()
            order.save(update_fields=[
                'payment_type', 'paid_amount', 'debt_amount', 'is_paid', 'status', 'closed_at',
            ])

            from kpi.models import WaiterKPI
            waiter_kpi = WaiterKPI.create_for_order(order)

        telegram_notification = send_checkout_notification(order)
        response_data = OrderSerializer(order).data
        from kpi.serializers import WaiterKPISerializer
        response_data['waiter_kpi'] = WaiterKPISerializer(waiter_kpi).data
        response_data['telegram_notification'] = telegram_notification
        return Response(response_data, status=status.HTTP_200_OK)
