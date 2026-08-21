from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authentication.permissions import IsAdminRole
from delivery.models import DeliveryOrder, DeliveryOrderItem
from kassa.models import CashExpense, CashSession
from kpi.models import EmployeeKPI
from restaurant.models import Order, OrderItem, User

from .serializers import KPIStatisticsQuerySerializer, StatisticsQuerySerializer


def _decimal(value):
    return value if value is not None else Decimal('0.00')


class StatisticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def _parse_period(self, request):
        serializer = StatisticsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        period_start = data.get('period_start')
        period_end = data.get('period_end')
        group_by = data.get('group_by', 'day')
        return period_start, period_end, group_by

    def _orders_queryset(self, period_start=None, period_end=None):
        queryset = (
            Order.objects.select_related('waiter', 'table', 'customer')
            .prefetch_related('items__product')
        )
        if period_start:
            queryset = queryset.filter(created_at__date__gte=period_start)
        if period_end:
            queryset = queryset.filter(created_at__date__lte=period_end)
        return queryset

    def _kpi_queryset(self, period_start=None, period_end=None):
        queryset = EmployeeKPI.objects.select_related('employee', 'created_by')
        if period_start:
            queryset = queryset.filter(period_end__gte=period_start)
        if period_end:
            queryset = queryset.filter(period_start__lte=period_end)
        return queryset

    def _delivery_queryset(self, period_start=None, period_end=None):
        queryset = (
            DeliveryOrder.objects.select_related('customer', 'created_by')
            .prefetch_related('items__product')
        )
        if period_start:
            queryset = queryset.filter(created_at__date__gte=period_start)
        if period_end:
            queryset = queryset.filter(created_at__date__lte=period_end)
        return queryset

    @action(detail=False, methods=['get'])
    def overview(self, request):
        period_start, period_end, group_by = self._parse_period(request)
        orders = self._orders_queryset(period_start, period_end)
        closed_orders = orders.filter(status='closed')
        cash_transactions = closed_orders.filter(cash_transaction__isnull=False)

        cash_total = cash_transactions.aggregate(total=Sum('cash_transaction__cash_amount'))['total']
        card_total = cash_transactions.aggregate(total=Sum('cash_transaction__card_amount'))['total']
        credit_total = cash_transactions.aggregate(total=Sum('cash_transaction__credit_amount'))['total']
        partner_total = cash_transactions.aggregate(total=Sum('cash_transaction__partner_amount'))['total']
        sales_total = closed_orders.aggregate(total=Sum('total_price'))['total']
        expenses = CashExpense.objects.all()
        if period_start:
            expenses = expenses.filter(created_at__date__gte=period_start)
        if period_end:
            expenses = expenses.filter(created_at__date__lte=period_end)
        expenses_total = _decimal(expenses.aggregate(total=Sum('amount'))['total'])

        closed_sessions = CashSession.objects.filter(
            status='closed',
            closing_balance__isnull=False,
        ).prefetch_related('transactions', 'expenses')
        if period_start:
            closed_sessions = closed_sessions.filter(closed_at__date__gte=period_start)
        if period_end:
            closed_sessions = closed_sessions.filter(closed_at__date__lte=period_end)
        kassa_difference = Decimal('0.00')
        for session in closed_sessions:
            cash_income = sum(
                (item.cash_amount for item in session.transactions.all()),
                Decimal('0.00'),
            )
            session_expenses = sum(
                (item.amount for item in session.expenses.all()),
                Decimal('0.00'),
            )
            expected_balance = session.opening_balance + cash_income - session_expenses
            kassa_difference += session.closing_balance - expected_balance

        active_cashiers = User.objects.filter(role='kassir', is_active=True).count()
        active_waiters = User.objects.filter(role='afitsant', is_active=True).count()

        active_orders = orders.exclude(status='closed')

        truncator = {
            'day': TruncDay('created_at'),
            'week': TruncWeek('created_at'),
            'month': TruncMonth('created_at'),
        }[group_by]

        grouped_orders = (
            orders.annotate(period=truncator)
            .values('period')
            .annotate(
                orders_count=Count('id'),
                closed_orders_count=Count('id', filter=Q(status='closed')),
                sales_total=Sum('total_price', filter=Q(status='closed')),
                cash_total=Sum('cash_transaction__cash_amount'),
                card_total=Sum('cash_transaction__card_amount'),
                credit_total=Sum('cash_transaction__credit_amount'),
                partner_offset=Sum('cash_transaction__partner_amount'),
            )
            .order_by('period')
        )

        waiter_stats = (
            orders.values('waiter_id', 'waiter__first_name', 'waiter__last_name', 'waiter__phone', 'waiter__role')
            .annotate(
                orders_count=Count('id'),
                closed_orders_count=Count('id', filter=Q(status='closed')),
                sales_total=Sum('total_price', filter=Q(status='closed')),
            )
            .order_by('-sales_total', 'waiter_id')
        )

        table_stats = (
            orders.values('table_id', 'table__number')
            .annotate(
                orders_count=Count('id'),
                closed_orders_count=Count('id', filter=Q(status='closed')),
                sales_total=Sum('total_price', filter=Q(status='closed')),
            )
            .order_by('-sales_total', 'table__number')
        )

        top_products = (
            OrderItem.objects.filter(order__in=closed_orders)
            .values('product_id', 'product__name')
            .annotate(
                quantity=Sum('quantity'),
                sales_total=Sum('subtotal'),
            )
            .order_by('-quantity', '-sales_total', 'product__name')[:10]
        )

        return Response(
            {
                'filters': {
                    'period_start': period_start,
                    'period_end': period_end,
                    'group_by': group_by,
                },
                'summary': {
                    'orders_total': orders.count(),
                    'closed_orders_total': closed_orders.count(),
                    'sales_total': _decimal(sales_total),
                    'cash_income': _decimal(cash_total),
                    'card_income': _decimal(card_total),
                    'credit_sales': _decimal(credit_total),
                    'partner_offset': _decimal(partner_total),
                    'expenses_total': _decimal(expenses_total),
                    'kassa_difference': kassa_difference,
                    'active_cashiers': active_cashiers,
                    'active_waiters': active_waiters,
                    'active_orders': active_orders.count(),
                },
                'period_totals': list(grouped_orders),
                'waiter_stats': list(waiter_stats),
                'table_stats': list(table_stats),
                'top_products': list(top_products),
            }
        )

    @action(detail=False, methods=['get'])
    def kpi(self, request):
        serializer = KPIStatisticsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        period_start = data.get('period_start')
        period_end = data.get('period_end')
        employee_id = data.get('employee')
        role = data.get('role')

        employee_roles = [
            'admin',
            'oshpaz',
            'kassir',
            'afitsant',
            'farrosh',
            'moykachi',
            'kuryer',
        ]
        employee_queryset = User.objects.filter(
            role__in=employee_roles,
            is_active=True,
        )
        if employee_id:
            employee_queryset = employee_queryset.filter(id=employee_id)
        if role:
            employee_queryset = employee_queryset.filter(role=role)

        queryset = self._kpi_queryset(period_start, period_end).exclude(
            kpi_type=EmployeeKPI.INSTANT_REWARD
        ).filter(employee__in=employee_queryset)

        regular_kpi_types = [
            EmployeeKPI.SALES_PERCENT,
            EmployeeKPI.EXPERIENCE_PERCENT,
            EmployeeKPI.SALARY_PERCENT,
        ]

        employees = employee_queryset.values(
            'id',
            'first_name',
            'last_name',
            'phone',
            'role',
            'salary',
        )
        employee_summary_map = {
            employee['id']: {
                'employee_id': employee['id'],
                'employee__first_name': employee['first_name'],
                'employee__last_name': employee['last_name'],
                'employee__phone': employee['phone'],
                'employee__role': employee['role'],
                'salary_base': _decimal(employee['salary']),
                'kpi_count': 0,
                'total_base_amount': Decimal('0.00'),
                'total_kpi_amount': Decimal('0.00'),
                'bonus_amount': Decimal('0.00'),
                'salary_advance_amount': Decimal('0.00'),
                'total_available_amount': Decimal('0.00'),
            }
            for employee in employees
        }


        for item in queryset.values('employee_id', 'kpi_type', 'base_amount', 'kpi_amount'):
            employee = employee_summary_map[item['employee_id']]
            employee['kpi_count'] += 1
            employee['total_base_amount'] += _decimal(item['base_amount'])
            if item['kpi_type'] == EmployeeKPI.BONUS:
                employee['bonus_amount'] += _decimal(item['kpi_amount'])
            elif item['kpi_type'] == EmployeeKPI.SALARY_ADVANCE:
                employee['salary_advance_amount'] += _decimal(item['kpi_amount'])
            elif item['kpi_type'] in regular_kpi_types:
                employee['total_kpi_amount'] += _decimal(item['kpi_amount'])

        employee_summary = []
        role_summary_map = {}
        for employee in employee_summary_map.values():
            employee['total_available_amount'] = (
                employee['salary_base']
                + employee['total_kpi_amount']
                + employee['bonus_amount']
                - employee['salary_advance_amount']
            )
            employee_summary.append(employee)
            role_data = role_summary_map.setdefault(
                employee['employee__role'],
                {
                    'employee__role': employee['employee__role'],
                    'employees_count': 0,
                    'kpi_count': 0,
                    'salary_base': Decimal('0.00'),
                    'total_base_amount': Decimal('0.00'),
                    'total_kpi_amount': Decimal('0.00'),
                    'bonus_amount': Decimal('0.00'),
                    'salary_advance_amount': Decimal('0.00'),
                    'total_available_amount': Decimal('0.00'),
                },
            )
            role_data['employees_count'] += 1
            role_data['kpi_count'] += employee['kpi_count']
            role_data['salary_base'] += employee['salary_base']
            role_data['total_base_amount'] += employee['total_base_amount']
            role_data['total_kpi_amount'] += employee['total_kpi_amount']
            role_data['bonus_amount'] += employee['bonus_amount']
            role_data['salary_advance_amount'] += employee['salary_advance_amount']
            role_data['total_available_amount'] += employee['total_available_amount']

        employee_summary = sorted(
            employee_summary,
            key=lambda item: (-item['total_available_amount'], item['employee_id']),
        )
        role_summary = sorted(role_summary_map.values(), key=lambda item: item['employee__role'])

        type_summary = (
            queryset.values('kpi_type')
            .annotate(
                kpi_count=Count('id'),
                total_base_amount=Sum('base_amount'),
                total_kpi_amount=Sum('kpi_amount'),
            )
            .order_by('kpi_type')
        )

        salary_summary = employee_summary
        regular_kpi_total = queryset.filter(kpi_type__in=regular_kpi_types).aggregate(total=Sum('kpi_amount'))['total']
        bonus_total = queryset.filter(kpi_type=EmployeeKPI.BONUS).aggregate(total=Sum('kpi_amount'))['total']
        salary_advance_total = queryset.filter(kpi_type=EmployeeKPI.SALARY_ADVANCE).aggregate(total=Sum('kpi_amount'))['total']
        salary_total = sum((item['salary_base'] for item in employee_summary), Decimal('0.00'))
        total_available = sum((item['total_available_amount'] for item in employee_summary), Decimal('0.00'))

        return Response(
            {
                'filters': {
                    'period_start': period_start,
                    'period_end': period_end,
                    'employee': employee_id,
                    'role': role,
                },
                'summary': {
                    'employees_count': len(employee_summary),
                    'kpi_count': queryset.count(),
                    'total_base_amount': _decimal(queryset.aggregate(total=Sum('base_amount'))['total']),
                    'salary_base': salary_total,
                    'total_kpi_amount': _decimal(regular_kpi_total),
                    'bonus_amount': _decimal(bonus_total),
                    'salary_advance_amount': _decimal(salary_advance_total),
                    'total_available_amount': total_available,
                },
                'salary_summary': salary_summary,
                'employee_summary': employee_summary,
                'role_summary': role_summary,
                'type_summary': list(type_summary),
            }
        )

    @action(detail=False, methods=['get'])
    def delivery(self, request):
        period_start, period_end, group_by = self._parse_period(request)
        orders = self._delivery_queryset(period_start, period_end)
        closed_orders = orders.filter(status='closed')
        paid_orders = closed_orders.filter(cash_transaction__isnull=False)

        cash_income = paid_orders.aggregate(total=Sum('cash_transaction__cash_amount'))['total']
        card_income = paid_orders.aggregate(total=Sum('cash_transaction__card_amount'))['total']
        credit_sales = paid_orders.aggregate(total=Sum('cash_transaction__credit_amount'))['total']
        sales_total = closed_orders.aggregate(total=Sum('total_price'))['total']
        delivery_fee_total = closed_orders.aggregate(total=Sum('delivery_fee'))['total']

        truncator = {
            'day': TruncDay('created_at'),
            'week': TruncWeek('created_at'),
            'month': TruncMonth('created_at'),
        }[group_by]
        period_totals = (
            orders.annotate(period=truncator)
            .values('period')
            .annotate(
                orders_count=Count('id'),
                closed_orders_count=Count('id', filter=Q(status='closed')),
                cancelled_orders_count=Count('id', filter=Q(status='cancelled')),
                sales_total=Sum('total_price', filter=Q(status='closed')),
                delivery_fee_total=Sum('delivery_fee', filter=Q(status='closed')),
                cash_income=Sum('cash_transaction__cash_amount', filter=Q(status='closed')),
                card_income=Sum('cash_transaction__card_amount', filter=Q(status='closed')),
                credit_sales=Sum('cash_transaction__credit_amount', filter=Q(status='closed')),
            )
            .order_by('period')
        )
        courier_stats = (
            orders.exclude(courier_name='')
            .values('courier_name', 'courier_phone')
            .annotate(
                orders_count=Count('id'),
                closed_orders_count=Count('id', filter=Q(status='closed')),
                active_orders_count=Count('id', filter=Q(status='new')),
                sales_total=Sum('total_price', filter=Q(status='closed')),
                delivery_fee_total=Sum('delivery_fee', filter=Q(status='closed')),
            )
            .order_by('-closed_orders_count', '-sales_total', 'courier_name')
        )
        top_products = (
            DeliveryOrderItem.objects.filter(delivery_order__in=closed_orders)
            .values('product_id', 'product__name')
            .annotate(quantity=Sum('quantity'), sales_total=Sum('subtotal'))
            .order_by('-quantity', '-sales_total', 'product__name')[:10]
        )

        return Response(
            {
                'filters': {
                    'period_start': period_start,
                    'period_end': period_end,
                    'group_by': group_by,
                },
                'summary': {
                    'orders_total': orders.count(),
                    'closed_orders_total': closed_orders.count(),
                    'cancelled_orders_total': orders.filter(status='cancelled').count(),
                    'new_orders_total': orders.filter(status='new').count(),
                    'sales_total': _decimal(sales_total),
                    'delivery_fee_total': _decimal(delivery_fee_total),
                    'cash_income': _decimal(cash_income),
                    'card_income': _decimal(card_income),
                    'credit_sales': _decimal(credit_sales),
                },
                'period_totals': list(period_totals),
                'courier_stats': list(courier_stats),
                'top_products': list(top_products),
            }
        )
