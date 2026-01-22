from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from . import metrics
from inflows.models import Inflow
from outflows.models import Outflow


@login_required(login_url='login')
def home(request):
    value_metrics = metrics.get_finance_metrics()

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
    expenses = metrics.get_expenses_by_category()

    context = {
        'metrics': value_metrics,
        'cash_flow': cash_flow,
        'expenses': expenses
    }

    return render(request, 'dashboard.html', context)
