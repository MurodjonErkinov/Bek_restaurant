from django.contrib import admin

from .models import EmployeeKPI


@admin.register(EmployeeKPI)
class EmployeeKPIAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'kpi_type',
        'period_start',
        'period_end',
        'percentage',
        'base_amount',
        'kpi_amount',
        'created_by',
    )
    list_filter = ('kpi_type', 'period_start', 'period_end')
    search_fields = (
        'employee__username',
        'employee__phone',
        'employee__first_name',
        'employee__last_name',
    )
    readonly_fields = (
        'kpi_amount',
        'created_by',
        'created_at',
        'updated_at',
    )
    date_hierarchy = 'period_end'

    def has_module_permission(self, request):
        return request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'

    def has_add_permission(self, request):
        return request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
