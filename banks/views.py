from rest_framework import generics
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from app.mixins import UserScopedAPIMixin, UserScopedFormMixin, UserScopedQuerySetMixin
from . import models, forms, serializers


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
        return super().form_valid(form)


class BankDetailView(LoginRequiredMixin, UserScopedQuerySetMixin, DetailView):
    model = models.Bank
    template_name = 'bank_detail.html'


class BankUpdateView(LoginRequiredMixin, UserScopedQuerySetMixin, UserScopedFormMixin, UpdateView):
    model = models.Bank
    template_name = 'bank_update.html'
    form_class = forms.BankForm
    success_url = reverse_lazy('bank_list')


class BankDeleteView(LoginRequiredMixin, UserScopedQuerySetMixin, DeleteView):
    model = models.Bank
    template_name = 'bank_delete.html'
    success_url = reverse_lazy('bank_list')


class BankCreateListAPIView(UserScopedAPIMixin, generics.ListCreateAPIView):
    queryset = models.Bank.objects.all()
    serializer_class = serializers.BankSerializer


class BankRetriveUpdateDestroyAPIView(UserScopedAPIMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Bank.objects.all()
    serializer_class = serializers.BankSerializer
