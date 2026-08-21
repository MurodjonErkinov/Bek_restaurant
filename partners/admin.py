from django.contrib import admin

from .models import Partner, PartnerTransaction


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'is_active', 'balance', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'phone')


@admin.register(PartnerTransaction)
class PartnerTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'partner', 'transaction_type', 'amount', 'order', 'created_by', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('partner__name', 'partner__phone', 'description')
    readonly_fields = (
        'partner', 'transaction_type', 'amount', 'order', 'description', 'created_by', 'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
