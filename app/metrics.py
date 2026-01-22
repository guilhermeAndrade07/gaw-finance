from django.utils.formats import number_format
from django.db.models import Sum
from datetime import date, timedelta
from banks.models import Bank
from inflows.models import Inflow
from outflows.models import Outflow
from categories.models import Category
import json


def get_finance_metrics():
    """Retorna métricas financeiras: saldo total, entradas/saídas do mês e saldo do mês"""

    # Data atual
    today = date.today()
    current_month = today.month
    current_year = today.year

    # 1. Saldo total de todos os bancos
    total_balance = Bank.objects.aggregate(Sum('balance'))['balance__sum'] or 0

    # 2. Entradas do mês
    inflows_month = Inflow.objects.filter(
        created_at__month=current_month,
        created_at__year=current_year
    ).aggregate(Sum('value'))['value__sum'] or 0

    # 3. Saídas do mês
    outflows_month = Outflow.objects.filter(
        created_at__month=current_month,
        created_at__year=current_year
    ).aggregate(Sum('value'))['value__sum'] or 0

    # 4. Saldo do mês (entradas - saídas)
    balance_month = inflows_month - outflows_month

    return {
        'total_balance': number_format(total_balance, decimal_pos=2, force_grouping=True),
        'inflows_month': number_format(inflows_month, decimal_pos=2, force_grouping=True),
        'outflows_month': number_format(outflows_month, decimal_pos=2, force_grouping=True),
        'balance_month': number_format(balance_month, decimal_pos=2, force_grouping=True),
    }


def get_monthly_cash_flow():
    """Retorna fluxo de caixa dos últimos 7 meses"""
    months_labels = []
    inflows_data = []
    outflows_data = []

    # Últimos 12 meses
    for i in range(7, -1, -1):
        date_obj = date.today() - timedelta(days=30 * i)
        month = date_obj.month
        year = date_obj.year

        # Entradas do mês
        inflow = Inflow.objects.filter(
            created_at__month=month,
            created_at__year=year
        ).aggregate(Sum('value'))['value__sum'] or 0

        # Saídas do mês
        outflow = Outflow.objects.filter(
            created_at__month=month,
            created_at__year=year
        ).aggregate(Sum('value'))['value__sum'] or 0

        months_labels.append(date_obj.strftime('%b/%Y'))
        inflows_data.append(float(inflow))
        outflows_data.append(float(outflow))

    return {
        'labels': json.dumps(months_labels),
        'inflows': json.dumps(inflows_data),
        'outflows': json.dumps(outflows_data),
    }


def get_expenses_by_category():
    """Retorna despesas agrupadas por categoria do mês atual"""
    categories_data = {}

    # Data atual
    today = date.today()
    current_month = today.month
    current_year = today.year

    categories = Category.objects.all()
    for category in categories:
        total = Outflow.objects.filter(
            category=category,
            created_at__month=current_month,
            created_at__year=current_year
        ).aggregate(Sum('value'))['value__sum'] or 0
        if total > 0:
            categories_data[category.name] = float(total)

    # Ordenar por valor decrescente
    sorted_categories = dict(sorted(categories_data.items(), key=lambda x: x[1], reverse=True))

    return {
        'labels': json.dumps(list(sorted_categories.keys())),
        'data': json.dumps(list(sorted_categories.values())),
    }
