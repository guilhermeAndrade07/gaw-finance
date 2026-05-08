from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views.generic import ListView

from .forms import AccountCreateForm
from .models import Account


class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    template_name = 'account_list.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        queryset = Account.objects.select_related('user')
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)


def account_create(request):
    if request.method == 'POST':
        form = AccountCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = AccountCreateForm()

    return render(request, 'account_create.html', {'form': form})
