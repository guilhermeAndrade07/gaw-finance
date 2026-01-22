from rest_framework import generics
from django.urls import reverse_lazy
from django.db.models import Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from . import models, forms, serializers


class PaymentListView(LoginRequiredMixin, ListView):
    model = models.Payment
    template_name = 'payment_list.html'
    context_object_name = 'payment'

    def get_queryset(self):
        queryset = super().get_queryset()
        title = self.request.GET.get('title')

        if title:
            queryset = queryset.filter(name__icontains=title)

        return queryset.order_by('date_payment')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        total = queryset.aggregate(Sum('value'))['value__sum'] or 0
        context['payment_total'] = total
        return context


class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = models.Payment
    template_name = 'payment_create.html'
    form_class = forms.PaymentForm
    success_url = reverse_lazy('payment_list')


class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = models.Payment
    template_name = 'payment_detail.html'


class PaymentUpdateView(LoginRequiredMixin, UpdateView):
    model = models.Payment
    template_name = 'payment_update.html'
    form_class = forms.PaymentForm
    success_url = reverse_lazy('payment_list')


class PaymentDeleteView(LoginRequiredMixin, DeleteView):
    model = models.Payment
    template_name = 'payment_delete.html'
    success_url = reverse_lazy('payment_list')


class PaymentCreateListAPIView(generics.ListCreateAPIView):
    queryset = models.Payment.objects.all()
    serializer_class = serializers.PaymentSerializer


class PaymentRetriveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Payment.objects.all()
    serializer_class = serializers.PaymentSerializer
