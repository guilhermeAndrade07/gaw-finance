from rest_framework import generics
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView

from app.mixins import UserScopedAPIMixin, UserScopedFormMixin, UserScopedQuerySetMixin
from . import models, services, serializers, forms


class BankListView(LoginRequiredMixin, UserScopedQuerySetMixin, ListView):
    model = models.Bank
    template_name = 'bank_list.html'
    context_object_name = 'banks'

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.GET.get('name')

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class BankCreateView(LoginRequiredMixin, UserScopedFormMixin, CreateView):
    model = models.Bank
    template_name = 'bank_create.html'
    form_class = forms.BankForm
    success_url = reverse_lazy('bank_list')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.balance = self.object.initial_balance
        self.object.save()
        self.handle_main_bank(form)
        return super().form_valid(form)

    def handle_main_bank(self, form):
        """Coordena a flag de banco principal sem violar a unicidade por usuario."""
        if form.cleaned_data.get('is_main'):
            services.set_main_bank(self.request.user, self.object)
        else:
            services.ensure_main_bank(self.request.user, self.object)


class BankDetailView(LoginRequiredMixin, UserScopedQuerySetMixin, DetailView):
    model = models.Bank
    template_name = 'bank_detail.html'


class BankUpdateView(LoginRequiredMixin, UserScopedQuerySetMixin, UserScopedFormMixin, UpdateView):
    model = models.Bank
    template_name = 'bank_update.html'
    form_class = forms.BankForm
    success_url = reverse_lazy('bank_list')

    def form_valid(self, form):
        self.object = form.save()
        if form.cleaned_data.get('is_main'):
            services.set_main_bank(self.request.user, self.object)
        else:
            services.ensure_main_bank(self.request.user, self.object)
        return super().form_valid(form)


class BankDeleteView(LoginRequiredMixin, UserScopedQuerySetMixin, DeleteView):
    model = models.Bank
    template_name = 'bank_delete.html'
    success_url = reverse_lazy('bank_list')


@login_required
@require_POST
def bank_set_main(request, pk):
    """POST-only: define o banco como principal (acao de estado)."""
    bank = get_object_or_404(models.Bank, pk=pk, user=request.user)
    services.set_main_bank(request.user, bank)
    return redirect('bank_list')


class BankCreateListAPIView(UserScopedAPIMixin, generics.ListCreateAPIView):
    queryset = models.Bank.objects.all()
    serializer_class = serializers.BankSerializer


class BankRetriveUpdateDestroyAPIView(UserScopedAPIMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Bank.objects.all()
    serializer_class = serializers.BankSerializer
