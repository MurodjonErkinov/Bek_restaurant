from decimal import Decimal

from rest_framework import serializers

from .models import Partner, PartnerTransaction


class PartnerSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Partner
        fields = ['id', 'name', 'phone', 'address', 'notes', 'is_active', 'balance', 'created_at']
        read_only_fields = ['id', 'balance', 'created_at']


class PartnerTransactionSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PartnerTransaction
        fields = [
            'id', 'partner', 'partner_name', 'transaction_type', 'amount', 'order',
            'description', 'created_by', 'created_by_name', 'created_at',
        ]
        read_only_fields = fields

    def get_created_by_name(self, transaction):
        return transaction.created_by.get_full_name() or transaction.created_by.phone


class PartnerAmountSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255)


class PartnerAdjustmentSerializer(PartnerAmountSerializer):
    direction = serializers.ChoiceField(choices=['increase', 'decrease'])
