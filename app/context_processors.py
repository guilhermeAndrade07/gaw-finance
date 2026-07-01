from django.db.models import Sum
from django.utils.formats import number_format
from inflows.models import Inflow
from outflows.models import Outflow
from banks.models import Bank


def total_balance(request):
    if not request.user.is_authenticated:
        return {'total_balance': '0,00'}

    total_initial = Bank.objects.filter(user=request.user).aggregate(Sum('initial_balance'))['initial_balance__sum'] or 0
    total_inflows = Inflow.objects.filter(user=request.user).aggregate(Sum('value'))['value__sum'] or 0
    total_outflows = Outflow.objects.filter(user=request.user).aggregate(Sum('value'))['value__sum'] or 0
    total = total_initial + total_inflows - total_outflows

    return {'total_balance': number_format(total, decimal_pos=2, force_grouping=True)}
