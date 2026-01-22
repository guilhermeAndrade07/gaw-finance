from rest_framework import generics
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from . import models, forms, serializers


class BankListView(LoginRequiredMixin, ListView):
    model = models.Bank
    template_name = 'bank_list.html'
    context_object_name = 'banks'

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.GET.get('name')

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class BankCreateView(LoginRequiredMixin, CreateView):
    model = models.Bank
    template_name = 'bank_create.html'
    form_class = forms.BankForm
    success_url = reverse_lazy('bank_list')


class BankDetailView(LoginRequiredMixin, DetailView):
    model = models.Bank
    template_name = 'bank_detail.html'


class BankUpdateView(LoginRequiredMixin, UpdateView):
    model = models.Bank
    template_name = 'bank_update.html'
    form_class = forms.BankForm
    success_url = reverse_lazy('bank_list')


class BankDeleteView(LoginRequiredMixin, DeleteView):
    model = models.Bank
    template_name = 'bank_delete.html'
    success_url = reverse_lazy('bank_list')


class BankCreateListAPIView(generics.ListCreateAPIView):
    queryset = models.Bank.objects.all()
    serializer_class = serializers.BankSerializer


class BankRetriveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Bank.objects.all()
    serializer_class = serializers.BankSerializer
