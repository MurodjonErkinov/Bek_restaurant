from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from authentication.permissions import (
    IsAdminOrCashier,
    IsAdminOrCashierOrWaiter,
    IsAdminRole,
    IsEmployee,
)
from kassa.models import CashSession, CashTransaction
from kassa.notifications import send_checkout_notification
from kassa.payments import parse_payment
from kassa.serializers import CashTransactionSerializer
from partners.models import Partner, PartnerTransaction

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
    permission_classes = [IsEmployee]


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsEmployee]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_available=True)
    serializer_class = ProductSerializer
    permission_classes = [IsEmployee]


class WaiterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        User.objects
        .filter(role='afitsant', is_active=True)
        .exclude(waiter_orders__status='new')
        .order_by('id')
    )
    serializer_class = WaiterSerializer
    permission_classes = [IsEmployee]


class RestaurantTableViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RestaurantTable.objects.filter(is_active=True).order_by('number')
    serializer_class = RestaurantTableSerializer
    permission_classes = [IsEmployee]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = (
        Order.objects
        .select_related('customer', 'waiter', 'table')
        .prefetch_related('items__product')
    )
    serializer_class = OrderSerializer

    def get_permissions(self):
        permission_classes = {
            'create': [IsAdminOrCashierOrWaiter],
            'update': [IsAdminRole],
            'partial_update': [IsAdminRole],
            'destroy': [IsAdminRole],
            'checkout': [IsAdminOrCashier],
        }.get(self.action, [IsEmployee])
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.exclude(status='closed')
        if self.request.user.role == 'afitsant' and not self.request.user.is_superuser:
            return queryset.filter(waiter=self.request.user)
        return queryset

    def perform_create(self, serializer):
        waiter = serializer.validated_data['waiter']
        if self.request.user.role == 'afitsant' and waiter != self.request.user:
            raise PermissionDenied('Afitsant faqat o‘z nomidan buyurtma ochishi mumkin.')
        if (
            self.request.user.role == 'afitsant'
            and serializer.validated_data.get('status', 'new') != 'new'
        ):
            raise PermissionDenied('Afitsant buyurtmani faqat new statusida ochishi mumkin.')
        serializer.save()

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

            try:
                payment = parse_payment(request.data, order.total_price)
            except ValueError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

            partner = None
            if payment['partner_amount'] > 0:
                partner_id = request.data.get('partner')
                if not partner_id:
                    return Response(
                        {'detail': 'partner_amount yuborilganda partner ID majburiy.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                partner = Partner.objects.select_for_update().filter(
                    pk=partner_id,
                    is_active=True,
                ).first()
                if partner is None:
                    return Response({'detail': 'Faol hamkor topilmadi.'}, status=status.HTTP_400_BAD_REQUEST)
                if payment['partner_amount'] > partner.balance:
                    return Response(
                        {'detail': 'partner_amount hamkor oldidagi mavjud qarzdan oshmasligi kerak.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            session_id = request.data.get('cash_session')
            sessions = CashSession.objects.select_for_update().filter(status='open')
            if request.user.role == 'kassir' and not request.user.is_superuser:
                sessions = sessions.filter(cashier=request.user)
                if session_id:
                    sessions = sessions.filter(pk=session_id)
                cash_session = sessions.order_by('-opened_at').first()
                if cash_session is None:
                    return Response(
                        {'detail': 'Kassirning ochiq kassa smenasi topilmadi.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                if not session_id:
                    return Response(
                        {'detail': 'Admin checkout uchun cash_session ID yuborishi kerak.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                cash_session = sessions.filter(pk=session_id).first()
                if cash_session is None:
                    return Response(
                        {'detail': 'Ochiq kassa smenasi topilmadi.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            order.payment_type = payment['payment_type']
            order.paid_amount = payment['paid_amount']
            order.debt_amount = payment['debt_amount']
            order.is_paid = payment['is_paid']
            order.status = 'closed'
            order.closed_at = timezone.now()
            order.save(update_fields=[
                'payment_type', 'paid_amount', 'debt_amount', 'is_paid', 'status', 'closed_at',
            ])

            cash_transaction = CashTransaction.objects.create(
                cash_session=cash_session,
                order=order,
                order_total=order.total_price,
                cash_amount=payment['cash_amount'],
                card_amount=payment['card_amount'],
                credit_amount=payment['credit_amount'],
                partner_amount=payment['partner_amount'],
            )
            if partner:
                PartnerTransaction.objects.create(
                    partner=partner,
                    transaction_type=PartnerTransaction.ORDER_OFFSET,
                    amount=payment['partner_amount'],
                    order=order,
                    description=f'Order #{order.id} bilan o‘zaro hisob',
                    created_by=request.user,
                )

        telegram_notification = send_checkout_notification(order)
        response_data = OrderSerializer(order).data
        response_data['cash_transaction'] = CashTransactionSerializer(cash_transaction).data
        response_data['telegram_notification'] = telegram_notification
        return Response(response_data, status=status.HTTP_200_OK)
