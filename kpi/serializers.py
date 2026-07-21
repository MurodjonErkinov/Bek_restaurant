from rest_framework import serializers

from .models import WaiterKPI


class WaiterKPISerializer(serializers.ModelSerializer):
    waiter_name = serializers.SerializerMethodField()
    table_number = serializers.IntegerField(source='table.number', read_only=True)

    class Meta:
        model = WaiterKPI
        fields = [
            'id',
            'waiter',
            'waiter_name',
            'order',
            'table',
            'table_number',
            'business_date',
            'sales_amount',
            'base_rate',
            'experience_bonus_rate',
            'total_rate',
            'commission_amount',
            'created_at',
        ]
        read_only_fields = fields

    def get_waiter_name(self, kpi):
        return kpi.waiter.get_full_name() or kpi.waiter.username
