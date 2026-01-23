from django.db.models import Sum
from banks.models import Bank


def total_balance(request):
    total = Bank.objects.aggregate(Sum('balance'))['balance__sum'] or 0
    return {'total_balance': total}
