from datetime import date

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from .models import WaiterKPI
from .serializers import WaiterKPISerializer


class WaiterKPIViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WaiterKPI.objects.select_related('waiter', 'order', 'table')
    serializer_class = WaiterKPISerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        waiter_id = self.request.query_params.get('waiter')
        business_date = self.request.query_params.get('business_date')

        if waiter_id:
            if not waiter_id.isdigit():
                raise ValidationError({'waiter': 'Afitsant ID si butun son bo‘lishi kerak.'})
            queryset = queryset.filter(waiter_id=waiter_id)

        if business_date:
            try:
                parsed_date = date.fromisoformat(business_date)
            except ValueError as exc:
                raise ValidationError(
                    {'business_date': 'Sana YYYY-MM-DD formatida bo‘lishi kerak.'}
                ) from exc
            queryset = queryset.filter(business_date=parsed_date)

        return queryset
