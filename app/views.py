from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import connections
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from kombu import Connection

from . import metrics
from banks.models import Bank
from inflows.models import Inflow
from outflows.models import Outflow

import json
import time

from django.core.cache import cache


def health_check(request):
    return JsonResponse({'status': 'ok'}, status=200)


def readiness_check(request):
    checks = {
        'database': False,
        'cache': False,
        'broker': False,
    }

    try:
        connections['default'].ensure_connection()
        checks['database'] = True
    except Exception:
        pass

    try:
        key = 'gaw_finance_readiness_probe'
        value = str(time.time())
        cache.set(key, value, 10)
        checks['cache'] = cache.get(key) == value
        cache.delete(key)
    except Exception:
        pass

    try:
        with Connection(settings.CELERY_BROKER_URL) as connection:
            connection.ensure_connection(max_retries=1, timeout=2)
            checks['broker'] = True
    except Exception:
        pass

    status_code = 200 if all(checks.values()) else 503
    return JsonResponse({'ready': all(checks.values()), 'checks': checks}, status=status_code)


@login_required(login_url='login')
def dashboard(request):
    bank_id = request.GET.get('bank')
    selected_bank = None

    if bank_id:
        selected_bank = get_object_or_404(Bank, pk=bank_id, user=request.user)

    value_metrics = metrics.get_finance_metrics(request.user, bank=selected_bank)
    investment_data = metrics.get_investment(request.user)
    value_metrics.update(investment_data)
    cash_flow = metrics.get_monthly_cash_flow(request.user, bank=selected_bank)

    inflows = Inflow.objects.filter(user=request.user)[:5]
    outflows = Outflow.objects.filter(user=request.user)[:7]

    for inflow in inflows:
        inflow.tipo = 'Entrada'
    for outflow in outflows:
        outflow.tipo = 'Saída'

    transactions = list(inflows) + list(outflows)
    transactions.sort(key=lambda x: x.created_at, reverse=True)
    latest_transactions = transactions[:10]

    month = request.GET.get('month')
    year = request.GET.get('year')

    if month and year:
        expenses = metrics.get_expenses_by_category(request.user, int(month), int(year), bank=selected_bank)
    else:
        expenses = metrics.get_expenses_by_category(request.user, bank=selected_bank)

    months_list = metrics.get_months_list()
    banks = Bank.objects.filter(user=request.user)

    goal_status = metrics.get_goal_status_counts(request.user)

    dashboard_data = {
        'cashFlow': {
            'labels': json.loads(cash_flow['labels']),
            'inflows': json.loads(cash_flow['inflows']),
            'outflows': json.loads(cash_flow['outflows']),
        },
        'expenses': {
            'labels': json.loads(expenses['labels']),
            'data': json.loads(expenses['data']),
        },
        'selectedBankId': str(selected_bank.id) if selected_bank else '',
    }

    context = {
        'metrics': value_metrics,
        'cash_flow': cash_flow,
        'expenses': expenses,
        'months_list': months_list,
        'banks': banks,
        'selected_bank_id': str(selected_bank.id) if selected_bank else '',
        'latest_transactions': latest_transactions,
        'goal_status': goal_status,
        'dashboard_data': dashboard_data,
    }

    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def get_expenses_by_month(request):
    month = request.GET.get('month')
    year = request.GET.get('year')
    bank_id = request.GET.get('bank')

    if not month or not year:
        return JsonResponse({'error': 'Mês e ano são obrigatórios'}, status=400)

    selected_bank = None
    if bank_id:
        selected_bank = get_object_or_404(Bank, pk=bank_id, user=request.user)

    try:
        expenses = metrics.get_expenses_by_category(request.user, int(month), int(year), bank=selected_bank)
        return JsonResponse({
            'labels': json.loads(expenses['labels']),
            'data': json.loads(expenses['data']),
            'success': True
        })
    except Exception:
        import logging
        logging.getLogger(__name__).exception('Erro ao buscar despesas por mes')
        return JsonResponse({'error': 'Erro ao processar os dados.', 'success': False}, status=500)
