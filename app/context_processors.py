from django.db.models import Sum
from django.utils.formats import number_format
from inflows.models import Inflow
from outflows.models import Outflow


def total_balance(request):

    total_inflows = Inflow.objects.aggregate(Sum('value'))['value__sum'] or 0
    total_outflows = Outflow.objects.aggregate(Sum('value'))['value__sum'] or 0
    total = total_inflows - total_outflows

    return {'total_balance': number_format(total, decimal_pos=2, force_grouping=True)}
