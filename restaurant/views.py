from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Customer, Order, Product
from .serializers import CategorySerializer, CustomerSerializer, OrderSerializer, ProductSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_available=True)
    serializer_class = ProductSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @action(detail=True, methods=['post'], url_path='checkout')
    def checkout(self, request, pk=None):
        with transaction.atomic():
            order = self.get_queryset().select_for_update().get(pk=pk)
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
            WaiterKPI.create_for_order(order)

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
