from django.contrib import admin

from .models import CashExpense, CashSession, CashTransaction


@admin.register(CashSession)
class CashSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'cashier', 'opening_balance', 'status', 'opened_at', 'closed_at')
    list_filter = ('status', 'cashier')


@admin.register(CashTransaction)
class CashTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'cash_session', 'order', 'order_total', 'cash_amount', 'credit_amount', 'created_at')
    readonly_fields = ('cash_session', 'order', 'order_total', 'cash_amount', 'credit_amount', 'created_at')


@admin.register(CashExpense)
class CashExpenseAdmin(admin.ModelAdmin):
    list_display = ('cash_session', 'amount', 'description', 'created_at')
