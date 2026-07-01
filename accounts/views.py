from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from .forms import AccountCreateForm, AccountEditForm
from .models import Account


class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    template_name = 'account_list.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        return Account.objects.select_related('user').filter(user=self.request.user)


def account_create(request):
    if request.method == 'POST':
        form = AccountCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = AccountCreateForm()

    return render(request, 'account_create.html', {'form': form})


@login_required(login_url='login')
def account_edit(request):
    account = get_object_or_404(Account, user=request.user)

    if request.method == 'POST':
        form = AccountEditForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso.')
            return redirect('account_list')
    else:
        form = AccountEditForm(instance=account, initial={
            'name': account.name,
            'username': account.user.username,
            'email': account.user.email,
        })

    return render(request, 'account_edit.html', {'form': form, 'account': account})
