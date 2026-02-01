from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from . import metrics
from inflows.models import Inflow
from outflows.models import Outflow
import json


@login_required(login_url='login')
def home(request):
    value_metrics = metrics.get_finance_metrics()
    investment_data = metrics.get_investment()
    value_metrics.update(investment_data)

    inflows = Inflow.objects.all()[:5]
    outflows = Outflow.objects.all()[:7]

    for inflow in inflows:
        inflow.tipo = 'Entrada'
    for outflow in outflows:
        outflow.tipo = 'Saída'

    transactions = list(inflows) + list(outflows)
    transactions.sort(key=lambda x: x.created_at, reverse=True)
    latest_transactions = transactions[:10]

    context = {
        'metrics': value_metrics,
        'latest_transactions': latest_transactions,
    }
    return render(request, 'home.html', context)


def dashboard(request):
    value_metrics = metrics.get_finance_metrics()
    cash_flow = metrics.get_monthly_cash_flow()
    
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    if month and year:
        expenses = metrics.get_expenses_by_category(int(month), int(year))
    else:
        expenses = metrics.get_expenses_by_category()
    
    months_list = metrics.get_months_list()

    context = {
        'metrics': value_metrics,
        'cash_flow': cash_flow,
        'expenses': expenses,
        'months_list': months_list,
    }

    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def get_expenses_by_month(request):
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    if not month or not year:
        return JsonResponse({'error': 'Mês e ano são obrigatórios'}, status=400)
    
    try:
        expenses = metrics.get_expenses_by_category(int(month), int(year))
        return JsonResponse({
            'labels': json.loads(expenses['labels']),
            'data': json.loads(expenses['data']),
            'success': True
        })
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)
