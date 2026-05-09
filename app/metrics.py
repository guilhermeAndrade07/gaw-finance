from django.utils.formats import number_format
from django.db.models import Sum
from datetime import date
from calendar import monthrange
from inflows.models import Inflow
from investments.models import InvestmentAsset
from outflows.models import Outflow
from categories.models import Category
from signatures.models import Signature
import json


def shift_months(base_date, months):
    month_index = base_date.month - 1 + months
    year = base_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return base_date.replace(year=year, month=month, day=day)


def get_finance_metrics(user):
    if not user or not user.is_authenticated:
        return {
            'total_balance': '0,00',
            'inflows_month': '0,00',
            'outflows_month': '0,00',
            'balance_month': '0,00',
            'total_signatures': '0,00',
        }

    today = date.today()
    current_month = today.month
    current_year = today.year

    inflows_month = Inflow.objects.filter(
        user=user,
        created_at__month=current_month,
        created_at__year=current_year
    ).aggregate(Sum('value'))['value__sum'] or 0

    outflows_month = Outflow.objects.filter(
        user=user,
        created_at__month=current_month,
        created_at__year=current_year
    ).aggregate(Sum('value'))['value__sum'] or 0

    balance_month = inflows_month - outflows_month

    # Saldo total calculado como (soma de todos os inflows) - (soma de todos os outflows)
    total_inflows = Inflow.objects.filter(user=user).aggregate(Sum('value'))['value__sum'] or 0
    total_outflows = Outflow.objects.filter(user=user).aggregate(Sum('value'))['value__sum'] or 0
    total_balance = total_inflows - total_outflows

    total_signatures = Signature.objects.filter(user=user, is_active=True).aggregate(Sum('value'))['value__sum'] or 0

    return {
        'total_balance': number_format(total_balance, decimal_pos=2, force_grouping=True),
        'inflows_month': number_format(inflows_month, decimal_pos=2, force_grouping=True),
        'outflows_month': number_format(outflows_month, decimal_pos=2, force_grouping=True),
        'balance_month': number_format(balance_month, decimal_pos=2, force_grouping=True),
        'total_signatures': number_format(total_signatures, decimal_pos=2, force_grouping=True),
    }


def get_monthly_cash_flow(user):
    if not user or not user.is_authenticated:
        return {
            'labels': json.dumps([]),
            'inflows': json.dumps([]),
            'outflows': json.dumps([]),
        }

    months_labels = []
    inflows_data = []
    outflows_data = []
    today = date.today()

    for i in range(7, -1, -1):
        date_obj = shift_months(today, -i)
        month = date_obj.month
        year = date_obj.year

        inflow = Inflow.objects.filter(
            user=user,
            created_at__month=month,
            created_at__year=year
        ).aggregate(Sum('value'))['value__sum'] or 0

        outflow = Outflow.objects.filter(
            user=user,
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


def get_expenses_by_category(user, month=None, year=None):
    categories_data = {}

    if not user or not user.is_authenticated:
        return {
            'labels': json.dumps([]),
            'data': json.dumps([]),
        }
    
    if month is None or year is None:
        today = date.today()
        month = today.month
        year = today.year

    categories = Category.objects.filter(user=user)
    for category in categories:
        total = Outflow.objects.filter(
            user=user,
            category=category,
            created_at__month=month,
            created_at__year=year
        ).aggregate(Sum('value'))['value__sum'] or 0
        if total > 0:
            categories_data[category.name] = float(total)

    sorted_categories = dict(sorted(categories_data.items(), key=lambda x: x[1], reverse=True))

    return {
        'labels': json.dumps(list(sorted_categories.keys())),
        'data': json.dumps(list(sorted_categories.values())),
    }


def get_months_list():
    months_pt_br = {
        1: 'Janeiro',
        2: 'Fevereiro',
        3: 'Março',
        4: 'Abril',
        5: 'Maio',
        6: 'Junho',
        7: 'Julho',
        8: 'Agosto',
        9: 'Setembro',
        10: 'Outubro',
        11: 'Novembro',
        12: 'Dezembro'
    }
    
    months_list = []
    today = date.today()
    
    for i in range(0, 8):
        date_obj = shift_months(today, -i)
        month_name = months_pt_br[date_obj.month]
        months_list.append({
            'month': date_obj.month,
            'year': date_obj.year,
            'display': f'{month_name} de {date_obj.year}',
            'value': f"{date_obj.year}-{date_obj.month:02d}"
        })
    
    return months_list


def get_investment(user):
    if not user or not user.is_authenticated:
        return {
            'total_investment': '0,00',
            'total_investment_value': 0.0
        }

    try:
        total_investment = InvestmentAsset.objects.filter(
            user=user,
            is_active=True
        ).aggregate(Sum('current_value'))['current_value__sum'] or 0
        return {
            'total_investment': number_format(total_investment, decimal_pos=2, force_grouping=True),
            'total_investment_value': float(total_investment)
        }
    except Exception:
        return {
            'total_investment': '0,00',
            'total_investment_value': 0.0
        }
