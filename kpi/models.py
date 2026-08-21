from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class EmployeeKPI(models.Model):
    SALES_PERCENT = 'sales_percent'
    EXPERIENCE_PERCENT = 'experience_percent'
    SALARY_PERCENT = 'salary_percent'
    BONUS = 'bonus'
    SALARY_ADVANCE = 'salary_advance'
    INSTANT_REWARD = 'instant_reward'
    KPI_TYPE_CHOICES = [
        (SALES_PERCENT, 'Yopilgan buyurtmalar summasidan 5%'),
        (EXPERIENCE_PERCENT, 'Bir yildan ortiq staj uchun 5%'),
        (SALARY_PERCENT, 'Oylikdan istalgan foiz'),
        (BONUS, 'Bonus'),
        (SALARY_ADVANCE, 'Oylik hisobidan qarz'),
        (INSTANT_REWARD, 'Mukofot'),
    ]
    FIXED_PERCENT = Decimal('5.00')

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='employee_kpis',
        on_delete=models.PROTECT,
        limit_choices_to={
            'role__in': [
                'admin',
                'oshpaz',
                'kassir',
                'afitsant',
                'farrosh',
                'moykachi',
                'kuryer',
            ],
        },
    )
    kpi_type = models.CharField(max_length=30, choices=KPI_TYPE_CHOICES)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    reward_date = models.DateField(null=True, blank=True)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=FIXED_PERCENT,
    )
    base_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    kpi_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False,
    )
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='created_employee_kpis',
        on_delete=models.PROTECT,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-period_end', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'kpi_type', 'period_start', 'period_end'],
                condition=Q(kpi_type__in=['sales_percent', 'experience_percent', 'salary_percent']),
                name='unique_regular_employee_kpi_period',
            ),
        ]

    def clean(self):
        super().clean()
        if self.employee.role == 'customer':
            raise ValidationError({'employee': 'Customer uchun KPI qo‘shib bo‘lmaydi.'})
        if self.kpi_type == self.INSTANT_REWARD:
            if not self.reward_date:
                raise ValidationError({'reward_date': 'Mukofot berilgan sana majburiy.'})
            self.period_start = None
            self.period_end = None
        else:
            if not self.period_start:
                raise ValidationError({'period_start': 'Davr boshlanish sanasi majburiy.'})
            if not self.period_end:
                raise ValidationError({'period_end': 'Davr tugash sanasi majburiy.'})
            if self.period_start > self.period_end:
                raise ValidationError({'period_end': 'Davr tugashi boshlanishidan oldin bo‘la olmaydi.'})
            self.reward_date = None
        if (
            self.employee.role in {'farrosh', 'moykachi'}
            and self.kpi_type not in {
                self.SALARY_PERCENT,
                self.BONUS,
                self.SALARY_ADVANCE,
                self.INSTANT_REWARD,
            }
        ):
            raise ValidationError(
                {
                    'kpi_type': (
                        'Farrosh va moykachiga faqat oylik, bonus, mukofot '
                        'yoki oylik hisobidan qarz qo‘shiladi.'
                    )
                }
            )
        if self.kpi_type in {self.SALES_PERCENT, self.EXPERIENCE_PERCENT}:
            if self.kpi_type == self.EXPERIENCE_PERCENT:
                joined_date = timezone.localdate(self.employee.date_joined)
                if joined_date + timedelta(days=365) > self.period_end:
                    raise ValidationError(
                        {'employee': 'Xodimning staji hali bir yildan oshmagan.'}
                    )
            self.percentage = self.FIXED_PERCENT
            if self.base_amount <= 0:
                raise ValidationError(
                    {'base_amount': 'Hisoblash uchun asosiy summa kiritilishi kerak.'}
                )
        elif self.kpi_type == self.SALARY_PERCENT:
            if self.percentage <= 0 or self.percentage > 100:
                raise ValidationError(
                    {'percentage': 'Foiz 0 dan katta va 100 dan oshmasligi kerak.'}
                )
            if self.employee.salary <= 0:
                raise ValidationError({'employee': 'Xodimning oyligi kiritilmagan.'})
            self.base_amount = self.employee.salary
        elif self.kpi_type in {self.BONUS, self.SALARY_ADVANCE, self.INSTANT_REWARD}:
            self.percentage = Decimal('100.00')
            if self.base_amount <= 0:
                raise ValidationError({'base_amount': 'Miqdor 0 dan katta bo‘lishi kerak.'})
        self.kpi_amount = (
            self.base_amount * self.percentage / Decimal('100')
        ).quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
