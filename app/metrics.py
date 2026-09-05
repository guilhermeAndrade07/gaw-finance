from datetime import date
from decimal import Decimal
from calendar import monthrange

from django.utils.formats import number_format
from django.db.models import Sum
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


def get_finance_metrics(user, bank=None):
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

    inflow_qs = Inflow.objects.filter(user=user)
    outflow_qs = Outflow.objects.filter(user=user)

    if bank:
        inflow_qs = inflow_qs.filter(bank=bank)
        outflow_qs = outflow_qs.filter(bank=bank)

    inflows_month = inflow_qs.filter(
        created_at__month=current_month,
        created_at__year=current_year
    ).aggregate(Sum('value'))['value__sum'] or 0

    outflows_month = outflow_qs.filter(
        created_at__month=current_month,
        created_at__year=current_year
    ).aggregate(Sum('value'))['value__sum'] or 0

    balance_month = inflows_month - outflows_month

    if bank:
        total_balance = bank.current_balance
    else:
        from banks.models import Bank
        total_initial = Bank.objects.filter(user=user).aggregate(Sum('initial_balance'))['initial_balance__sum'] or 0
        total_inflows = inflow_qs.aggregate(Sum('value'))['value__sum'] or 0
        total_outflows = outflow_qs.aggregate(Sum('value'))['value__sum'] or 0
        total_balance = total_initial + total_inflows - total_outflows

    total_signatures = Signature.objects.filter(user=user, is_active=True).aggregate(Sum('value'))['value__sum'] or 0

    return {
        'total_balance': number_format(total_balance, decimal_pos=2, force_grouping=True),
        'inflows_month': number_format(inflows_month, decimal_pos=2, force_grouping=True),
        'outflows_month': number_format(outflows_month, decimal_pos=2, force_grouping=True),
        'balance_month': number_format(balance_month, decimal_pos=2, force_grouping=True),
        'total_signatures': number_format(total_signatures, decimal_pos=2, force_grouping=True),
    }


def get_monthly_cash_flow(user, bank=None):
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

        inflow_qs = Inflow.objects.filter(
            user=user,
            created_at__month=month,
            created_at__year=year
        )
        outflow_qs = Outflow.objects.filter(
            user=user,
            created_at__month=month,
            created_at__year=year
        )

        if bank:
            inflow_qs = inflow_qs.filter(bank=bank)
            outflow_qs = outflow_qs.filter(bank=bank)

        inflow = inflow_qs.aggregate(Sum('value'))['value__sum'] or 0
        outflow = outflow_qs.aggregate(Sum('value'))['value__sum'] or 0

        months_labels.append(date_obj.strftime('%b/%Y'))
        inflows_data.append(float(inflow))
        outflows_data.append(float(outflow))

    return {
        'labels': json.dumps(months_labels),
        'inflows': json.dumps(inflows_data),
        'outflows': json.dumps(outflows_data),
    }


def get_expenses_by_category(user, month=None, year=None, bank=None):
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
        outflow_qs = Outflow.objects.filter(
            user=user,
            category=category,
            created_at__month=month,
            created_at__year=year
        )
        if bank:
            outflow_qs = outflow_qs.filter(bank=bank)
        total = outflow_qs.aggregate(Sum('value'))['value__sum'] or 0
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


def get_goal_progress(user, month=None, year=None):
    if not user or not user.is_authenticated:
        return {
            'labels': json.dumps([]),
            'percentages': json.dumps([]),
            'spent': json.dumps([]),
            'goals': json.dumps([]),
        }

    if month is None or year is None:
        today = date.today()
        month = today.month
        year = today.year

    from goals.models import MonthlyGoal

    goals = MonthlyGoal.objects.filter(
        user=user, month=month, year=year,
    ).select_related('category')

    progress_list = []
    for goal in goals:
        if goal.category is None:
            outflow_qs = Outflow.objects.filter(
                user=user, category__isnull=True,
                created_at__month=month, created_at__year=year,
            )
        else:
            outflow_qs = Outflow.objects.filter(
                user=user, category=goal.category,
                created_at__month=month, created_at__year=year,
            )
        spent = outflow_qs.aggregate(Sum('value'))['value__sum'] or Decimal('0')

        goal_value = Decimal(goal.value) if not isinstance(goal.value, Decimal) else goal.value
        if goal_value > 0:
            percentage = float(round((spent / goal_value) * Decimal('100'), 2))
        else:
            percentage = 0.0

        progress_list.append({
            'name': goal.category_display,
            'goal': float(goal_value),
            'spent': float(spent),
            'percentage': percentage,
        })

    progress_list.sort(key=lambda x: x['percentage'], reverse=True)

    return {
        'labels': json.dumps([item['name'] for item in progress_list]),
        'percentages': json.dumps([item['percentage'] for item in progress_list]),
        'spent': json.dumps([item['spent'] for item in progress_list]),
        'goals': json.dumps([item['goal'] for item in progress_list]),
    }


def get_goal_status_counts(user, month=None, year=None):
    if not user or not user.is_authenticated:
        return {'ok': 0, 'warning': 0, 'exceeded': 0, 'total': 0}

    if month is None or year is None:
        today = date.today()
        month = today.month
        year = today.year

    from goals.models import MonthlyGoal

    goals = MonthlyGoal.objects.filter(
        user=user, month=month, year=year,
    ).select_related('category')

    ok = warning = exceeded = 0
    for goal in goals:
        if goal.category is None:
            outflow_qs = Outflow.objects.filter(
                user=user, category__isnull=True,
                created_at__month=month, created_at__year=year,
            )
        else:
            outflow_qs = Outflow.objects.filter(
                user=user, category=goal.category,
                created_at__month=month, created_at__year=year,
            )
        spent = outflow_qs.aggregate(Sum('value'))['value__sum'] or Decimal('0')

        goal_value = Decimal(goal.value) if not isinstance(goal.value, Decimal) else goal.value
        if goal_value > 0:
            ratio = float(spent / goal_value)
        else:
            ratio = 0.0

        if ratio > 1.0:
            exceeded += 1
        elif ratio >= 0.7:
            warning += 1
        else:
            ok += 1

    return {
        'ok': ok,
        'warning': warning,
        'exceeded': exceeded,
        'total': goals.count(),
    }
