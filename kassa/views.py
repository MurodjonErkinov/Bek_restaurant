from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from authentication.permissions import IsAdminOrCashier

from .models import CashExpense, CashSession, CashTransaction
from .serializers import CashExpenseSerializer, CashSessionSerializer, CashTransactionSerializer


class CashSessionViewSet(viewsets.ModelViewSet):
    queryset = CashSession.objects.select_related('cashier').all()
    serializer_class = CashSessionSerializer
    permission_classes = [IsAdminOrCashier]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == 'kassir' and not self.request.user.is_superuser:
            return queryset.filter(cashier=self.request.user)
        return queryset

    def perform_create(self, serializer):
        cashier = serializer.validated_data['cashier']
        if self.request.user.role == 'kassir' and cashier != self.request.user:
            raise PermissionDenied('Kassir faqat o‘z nomidan kassa ochishi mumkin.')
        serializer.save()

    def perform_update(self, serializer):
        cashier = serializer.validated_data.get('cashier', serializer.instance.cashier)
        if self.request.user.role == 'kassir' and cashier != self.request.user:
            raise PermissionDenied('Kassir kassa egasini o‘zgartira olmaydi.')
        serializer.save()

    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        return Response(self.get_object().report())

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        try:
            closing_balance = Decimal(str(request.data['closing_balance']))
        except (InvalidOperation, KeyError, TypeError, ValueError):
            return Response({'detail': 'closing_balance majburiy son.'}, status=status.HTTP_400_BAD_REQUEST)
        if not closing_balance.is_finite() or closing_balance < 0:
            return Response({'detail': 'closing_balance manfiy bo‘la olmaydi.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            session = self.get_queryset().select_for_update().get(pk=pk)
            if session.status != 'open':
                return Response({'detail': 'Kassa avval yopilgan.'}, status=status.HTTP_400_BAD_REQUEST)
            session.closing_balance = closing_balance
            session.closed_at = timezone.now()
            session.status = 'closed'
            session.save(update_fields=['closing_balance', 'closed_at', 'status'])
        return Response(session.report())


class CashExpenseViewSet(viewsets.ModelViewSet):
    queryset = CashExpense.objects.select_related('cash_session').all()
    serializer_class = CashExpenseSerializer
    permission_classes = [IsAdminOrCashier]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == 'kassir' and not self.request.user.is_superuser:
            return queryset.filter(cash_session__cashier=self.request.user)
        return queryset

    def perform_create(self, serializer):
        session = serializer.validated_data['cash_session']
        if self.request.user.role == 'kassir' and session.cashier != self.request.user:
            raise PermissionDenied('Kassir faqat o‘z kassasiga chiqim qo‘sha oladi.')
        serializer.save()

    def perform_update(self, serializer):
        session = serializer.validated_data.get(
            'cash_session',
            serializer.instance.cash_session,
        )
        if self.request.user.role == 'kassir' and session.cashier != self.request.user:
            raise PermissionDenied('Kassir chiqimni boshqa kassaga o‘tkaza olmaydi.')
        serializer.save()


class CashTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CashTransaction.objects.select_related('cash_session', 'order').all()
    serializer_class = CashTransactionSerializer
    permission_classes = [IsAdminOrCashier]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == 'kassir' and not self.request.user.is_superuser:
            return queryset.filter(cash_session__cashier=self.request.user)
        return queryset
