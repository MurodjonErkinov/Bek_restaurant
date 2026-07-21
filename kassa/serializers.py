from rest_framework import serializers

from .models import CashExpense, CashSession, CashTransaction


class CashSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashSession
        fields = [
            'id', 'cashier', 'opening_balance', 'opened_at', 'status',
            'closing_balance', 'closed_at', 'notes',
        ]
        read_only_fields = ['id', 'opened_at', 'status', 'closing_balance', 'closed_at']

    def validate_cashier(self, cashier):
        if cashier.role != 'kassir':
            raise serializers.ValidationError('Faqat kassir uchun kassa ochish mumkin.')
        if CashSession.objects.filter(cashier=cashier, status='open').exists():
            raise serializers.ValidationError('Bu kassirda ochiq kassa smenasi bor.')
        return cashier


class CashExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashExpense
        fields = ['id', 'cash_session', 'amount', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_cash_session(self, session):
        if session.status != 'open':
            raise serializers.ValidationError('Yopilgan kassaga chiqim qo‘shib bo‘lmaydi.')
        return session


class CashTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashTransaction
        fields = ['id', 'cash_session', 'order', 'order_total', 'cash_amount', 'credit_amount', 'created_at']
        read_only_fields = fields
