from django.contrib import admin

from .models import WaiterKPI


@admin.register(WaiterKPI)
class WaiterKPIAdmin(admin.ModelAdmin):
    list_display = (
        'business_date', 'waiter', 'order', 'table', 'sales_amount',
        'total_rate', 'commission_amount',
    )
    list_filter = ('business_date', 'waiter')
    search_fields = ('waiter__username', 'order__id')
    readonly_fields = (
        'waiter', 'order', 'table', 'business_date', 'sales_amount', 'base_rate',
        'experience_bonus_rate', 'total_rate', 'commission_amount', 'created_at',
    )
