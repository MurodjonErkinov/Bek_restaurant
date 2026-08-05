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
        open_sessions = CashSession.objects.filter(cashier=cashier, status='open')
        if self.instance:
            open_sessions = open_sessions.exclude(pk=self.instance.pk)
        if open_sessions.exists():
            raise serializers.ValidationError('Bu kassirda ochiq kassa smenasi bor.')
        return cashier

    def validate_opening_balance(self, value):
        if value < 0:
            raise serializers.ValidationError('opening_balance manfiy bo‘la olmaydi.')
        return value


class CashExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashExpense
        fields = ['id', 'cash_session', 'amount', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_cash_session(self, session):
        if session.status != 'open':
            raise serializers.ValidationError('Yopilgan kassaga chiqim qo‘shib bo‘lmaydi.')
        return session

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('amount 0 dan katta bo‘lishi kerak.')
        return value


class CashTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashTransaction
        fields = ['id', 'cash_session', 'order', 'order_total', 'cash_amount', 'credit_amount', 'created_at']
        read_only_fields = fields
