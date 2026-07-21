from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CashExpense, CashSession, CashTransaction
from .serializers import CashExpenseSerializer, CashSessionSerializer, CashTransactionSerializer


class CashSessionViewSet(viewsets.ModelViewSet):
    queryset = CashSession.objects.select_related('cashier').all()
    serializer_class = CashSessionSerializer

    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        return Response(self.get_object().report())

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        try:
            closing_balance = Decimal(str(request.data['closing_balance']))
        except (KeyError, ValueError):
            return Response({'detail': 'closing_balance majburiy son.'}, status=status.HTTP_400_BAD_REQUEST)
        if closing_balance < 0:
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


class CashTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CashTransaction.objects.select_related('cash_session', 'order').all()
    serializer_class = CashTransactionSerializer


