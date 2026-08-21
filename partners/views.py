from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from authentication.permissions import IsAdminOrCashier, IsAdminRole

from .models import Partner, PartnerTransaction
from .serializers import (
    PartnerAdjustmentSerializer,
    PartnerAmountSerializer,
    PartnerSerializer,
    PartnerTransactionSerializer,
)


class PartnerViewSet(viewsets.ModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer

    def get_permissions(self):
        admin_actions = {
            'create', 'update', 'partial_update', 'destroy',
            'purchase_debt', 'payment', 'adjustment',
        }
        permission = IsAdminRole if self.action in admin_actions else IsAdminOrCashier
        return [permission()]

    def _create_transaction(self, request, partner, transaction_type, data):
        partner_transaction = PartnerTransaction.objects.create(
            partner=partner,
            transaction_type=transaction_type,
            amount=data['amount'],
            description=data['description'],
            created_by=request.user,
        )
        return Response(
            {
                'transaction': PartnerTransactionSerializer(partner_transaction).data,
                'balance': partner.balance,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        partner = self.get_object()
        return Response({'partner_id': partner.id, 'partner_name': partner.name, 'balance': partner.balance})

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        partner = self.get_object()
        queryset = partner.transactions.select_related('created_by', 'order')
        return Response(PartnerTransactionSerializer(queryset, many=True).data)

    @action(detail=True, methods=['post'], url_path='purchase-debt')
    def purchase_debt(self, request, pk=None):
        serializer = PartnerAmountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            partner = Partner.objects.select_for_update().get(pk=pk)
            return self._create_transaction(
                request,
                partner,
                PartnerTransaction.PURCHASE_DEBT,
                serializer.validated_data,
            )

    @action(detail=True, methods=['post'])
    def payment(self, request, pk=None):
        serializer = PartnerAmountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            partner = Partner.objects.select_for_update().get(pk=pk)
            if serializer.validated_data['amount'] > partner.balance:
                return Response(
                    {'detail': 'To‘lov hamkor oldidagi mavjud qarzdan oshmasligi kerak.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return self._create_transaction(
                request,
                partner,
                PartnerTransaction.PAYMENT,
                serializer.validated_data,
            )

    @action(detail=True, methods=['post'])
    def adjustment(self, request, pk=None):
        serializer = PartnerAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        transaction_type = (
            PartnerTransaction.ADJUSTMENT_INCREASE
            if data['direction'] == 'increase'
            else PartnerTransaction.ADJUSTMENT_DECREASE
        )
        with transaction.atomic():
            partner = Partner.objects.select_for_update().get(pk=pk)
            if data['direction'] == 'decrease' and data['amount'] > partner.balance:
                return Response(
                    {'detail': 'Kamaytirish summasi mavjud qarzdan oshmasligi kerak.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return self._create_transaction(request, partner, transaction_type, data)
