from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from authentication.permissions import IsAdminOrCashier, IsAdminRole
from kassa.models import CashSession, CashTransaction
from kassa.notifications import send_delivery_checkout_notification
from kassa.payments import parse_payment
from kassa.serializers import CashTransactionSerializer
from .models import DeliveryOrder
from .serializers import DeliveryOrderSerializer


class DeliveryOrderViewSet(viewsets.ModelViewSet):
    queryset = DeliveryOrder.objects.select_related('customer', 'created_by').prefetch_related('items__product')
    serializer_class = DeliveryOrderSerializer

    def get_permissions(self):
        permission_classes = {
            'create': [IsAdminOrCashier],
            'update': [IsAdminOrCashier],
            'partial_update': [IsAdminOrCashier],
            'destroy': [IsAdminRole],
            'payment': [IsAdminOrCashier],
        }.get(self.action, [IsAdminOrCashier])
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.status != 'new':
            raise PermissionDenied('Bu statusdagi delivery buyurtmani tahrirlab bo‘lmaydi.')
        serializer.save()

    @action(detail=True, methods=['post'])
    def payment(self, request, pk=None):
        with transaction.atomic():
            order = DeliveryOrder.objects.select_for_update().get(pk=pk)
            if order.status != 'new':
                return Response({'detail': 'To‘lov faqat ochiq delivery buyurtma uchun olinadi.'}, status=status.HTTP_400_BAD_REQUEST)
            if hasattr(order, 'cash_transaction'):
                return Response({'detail': 'Bu buyurtma uchun to‘lov avval qabul qilingan.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                payment = parse_payment(request.data, order.total_price)
            except ValueError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

            session_id = request.data.get('cash_session')
            sessions = CashSession.objects.select_for_update().filter(status='open')
            if request.user.role == 'kassir' and not request.user.is_superuser:
                sessions = sessions.filter(cashier=request.user)
                if session_id:
                    sessions = sessions.filter(pk=session_id)
                cash_session = sessions.order_by('-opened_at').first()
            else:
                cash_session = sessions.filter(pk=session_id).first() if session_id else None
            if cash_session is None:
                return Response({'detail': 'Ochiq kassa smenasi topilmadi.'}, status=status.HTTP_400_BAD_REQUEST)

            order.payment_type = payment['payment_type']
            order.paid_amount = payment['paid_amount']
            order.debt_amount = payment['debt_amount']
            order.is_paid = payment['is_paid']
            order.status = 'closed'
            order.closed_at = timezone.now()
            order.save(update_fields=['payment_type', 'paid_amount', 'debt_amount', 'is_paid', 'status', 'closed_at'])
            cash_transaction = CashTransaction.objects.create(
                cash_session=cash_session,
                delivery_order=order,
                order_total=order.total_price,
                cash_amount=payment['cash_amount'],
                card_amount=payment['card_amount'],
                credit_amount=payment['credit_amount'],
            )

        telegram_notification = send_delivery_checkout_notification(order)
        response_data = self.get_serializer(order).data
        response_data['cash_transaction'] = CashTransactionSerializer(cash_transaction).data
        response_data['telegram_notification'] = telegram_notification
        return Response(response_data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        if request.user.role not in {'admin', 'kassir'} and not request.user.is_superuser:
            raise PermissionDenied('Delivery buyurtmani faqat admin yoki kassir bekor qila oladi.')
        reason = str(request.data.get('cancel_reason', '')).strip()
        if not reason:
            return Response({'detail': 'cancel_reason majburiy.'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            order = DeliveryOrder.objects.select_for_update().get(pk=pk)
            if order.status in {'closed', 'cancelled'}:
                return Response({'detail': 'Bu buyurtmani bekor qilib bo‘lmaydi.'}, status=status.HTTP_400_BAD_REQUEST)
            order.status = 'cancelled'
            order.cancelled_at = timezone.now()
            order.cancel_reason = reason
            order.save(update_fields=['status', 'cancelled_at', 'cancel_reason'])
        return Response(self.get_serializer(order).data)
