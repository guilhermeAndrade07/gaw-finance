from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from categories.models import Category


MONTHS_PT_BR = {
    1: 'Janeiro',
    2: 'Fevereiro',
    3: 'Marco',
    4: 'Abril',
    5: 'Maio',
    6: 'Junho',
    7: 'Julho',
    8: 'Agosto',
    9: 'Setembro',
    10: 'Outubro',
    11: 'Novembro',
    12: 'Dezembro',
}


class MonthlyGoal(models.Model):

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='goals',
        null=True, blank=True,
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='goals',
        null=True, blank=True,
    )
    value = models.DecimalField(max_digits=20, decimal_places=2)
    month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    year = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', '-month', 'category__name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category', 'month', 'year'],
                name='unique_goal_per_user_category_month_year',
                condition=Q(category__isnull=False),
            ),
            models.UniqueConstraint(
                fields=['user', 'month', 'year'],
                name='unique_goal_per_user_null_category_month_year',
                condition=Q(category__isnull=True),
            ),
        ]

    def __str__(self):
        category_name = self.category.name if self.category else 'Sem categoria'
        month_name = MONTHS_PT_BR.get(self.month, str(self.month))
        return f'{category_name} - {month_name}/{self.year} - R$ {self.value}'

    @property
    def category_display(self):
        return self.category.name if self.category else 'Sem categoria'
