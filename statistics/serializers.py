from rest_framework import serializers


class StatisticsQuerySerializer(serializers.Serializer):
    period_start = serializers.DateField(required=False)
    period_end = serializers.DateField(required=False)
    group_by = serializers.ChoiceField(
        choices=['day', 'week', 'month'],
        required=False,
        default='day',
    )


class KPIStatisticsQuerySerializer(serializers.Serializer):
    period_start = serializers.DateField(required=False)
    period_end = serializers.DateField(required=False)
    employee = serializers.IntegerField(required=False)
    role = serializers.CharField(required=False)

