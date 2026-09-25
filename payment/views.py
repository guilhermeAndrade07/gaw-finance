from rest_framework import generics
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from app.mixins import UserScopedAPIMixin, UserScopedFormMixin, UserScopedQuerySetMixin
from . import models, forms, serializers
from .services import (
    assign_invoice_to_payment,
    mark_invoice_paid,
    mark_invoice_unpaid,
    mark_payment_paid,
    mark_payment_unpaid,
    register_payment,
)


class PaymentListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        from django.urls import reverse
        url = reverse('invoice_list')
        query = request.GET.urlencode()
        if query:
            url = f'{url}?{query}'
        return HttpResponseRedirect(url)


class PaymentCreateView(LoginRequiredMixin, UserScopedFormMixin, CreateView):
    model = models.Payment
    template_name = 'payment_create.html'
    form_class = forms.PaymentForm
    success_url = reverse_lazy('invoice_list')

    def get_initial(self):
        initial = super().get_initial()
        card_id = self.request.GET.get('card')

        if card_id and models.CreditCard.objects.filter(
            id=card_id,
            user=self.request.user,
            active=True,
        ).exists():
            initial['card'] = card_id

        return initial

    def get_success_url(self):
        if getattr(self.object, 'card_id', None):
            return f'{self.success_url}?card={self.object.card_id}'

        return str(self.success_url)

    def form_valid(self, form):
        try:
            self.object = register_payment(
                user=self.request.user,
                card=form.cleaned_data['card'],
                name=form.cleaned_data['name'],
                description=form.cleaned_data.get('description'),
                category=form.cleaned_data.get('category'),
                date_payment=form.cleaned_data['date_payment'],
                value=form.cleaned_data['value'],
                parcelas=form.cleaned_data.get('parcelas') or 1,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        if self.object.card_id:
            return HttpResponseRedirect(f'{self.success_url}?card={self.object.card_id}')

        return HttpResponseRedirect(str(self.success_url))


class PaymentDetailView(LoginRequiredMixin, UserScopedQuerySetMixin, DetailView):
    model = models.Payment
    template_name = 'payment_detail.html'


class PaymentUpdateView(LoginRequiredMixin, UserScopedQuerySetMixin, UserScopedFormMixin, UpdateView):
    model = models.Payment
    template_name = 'payment_update.html'
    form_class = forms.PaymentForm
    success_url = reverse_lazy('invoice_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        if getattr(self.object, 'card_id', None) and getattr(self.object, 'date_payment', None):
            assign_invoice_to_payment(self.object)
        return response

    def get_success_url(self):
        if getattr(self.object, 'card_id', None):
            return f'{self.success_url}?card={self.object.card_id}'
        return str(self.success_url)


class PaymentDeleteView(LoginRequiredMixin, UserScopedQuerySetMixin, DeleteView):
    model = models.Payment
    template_name = 'payment_delete.html'
    success_url = reverse_lazy('invoice_list')


class CreditCardListView(LoginRequiredMixin, UserScopedQuerySetMixin, ListView):
    model = models.CreditCard
    template_name = 'credit_card_list.html'
    context_object_name = 'cards'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('bank')
        name = self.request.GET.get('name')

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class CreditCardCreateView(LoginRequiredMixin, UserScopedFormMixin, CreateView):
    model = models.CreditCard
    template_name = 'credit_card_create.html'
    form_class = forms.CreditCardForm
    success_url = reverse_lazy('credit_card_list')


class CreditCardDetailView(LoginRequiredMixin, UserScopedQuerySetMixin, DetailView):
    model = models.CreditCard
    template_name = 'credit_card_detail.html'

    def get_queryset(self):
        return super().get_queryset().select_related('bank')


class CreditCardUpdateView(LoginRequiredMixin, UserScopedQuerySetMixin, UserScopedFormMixin, UpdateView):
    model = models.CreditCard
    template_name = 'credit_card_update.html'
    form_class = forms.CreditCardForm
    success_url = reverse_lazy('credit_card_list')


class CreditCardDeleteView(LoginRequiredMixin, UserScopedQuerySetMixin, DeleteView):
    model = models.CreditCard
    template_name = 'credit_card_delete.html'
    success_url = reverse_lazy('credit_card_list')


class PaymentCreateListAPIView(UserScopedAPIMixin, generics.ListCreateAPIView):
    queryset = models.Payment.objects.all()
    serializer_class = serializers.PaymentSerializer


class PaymentRetriveUpdateDestroyAPIView(UserScopedAPIMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Payment.objects.all()
    serializer_class = serializers.PaymentSerializer


class PaymentMarkAsPaidView(LoginRequiredMixin, View):
    def post(self, request, pk):
        get_object_or_404(models.Payment, pk=pk, user=request.user)
        payment = mark_payment_paid(user=request.user, payment_id=pk)

        if not getattr(payment, '_status_changed', False):
            return JsonResponse({'success': True, 'already_paid': True})
        return JsonResponse({'success': True})


class PaymentMarkAsUnpaidView(LoginRequiredMixin, View):
    def post(self, request, pk):
        get_object_or_404(models.Payment, pk=pk, user=request.user)
        payment = mark_payment_unpaid(user=request.user, payment_id=pk)

        if not getattr(payment, '_status_changed', False):
            return JsonResponse({'success': True, 'already_unpaid': True})
        return JsonResponse({'success': True})


class InvoiceListView(LoginRequiredMixin, ListView):
    model = models.Invoice
    template_name = 'invoice_list.html'
    context_object_name = 'invoices'

    def _show_hidden(self):
        return self.request.GET.get('show_hidden') == '1'

    def _selected_card(self):
        card_id = self.request.GET.get('card')
        if not card_id:
            return None
        try:
            return models.CreditCard.objects.get(id=int(card_id), user=self.request.user)
        except (models.CreditCard.DoesNotExist, ValueError, TypeError):
            return None

    def get_queryset(self):
        selected_card = self._selected_card()
        if not selected_card:
            return models.Invoice.objects.none()

        queryset = super().get_queryset().filter(card=selected_card).select_related('card', 'card__bank')

        if self._show_hidden():
            queryset = queryset.filter(status=models.Invoice.PAID)
        else:
            queryset = queryset.exclude(status=models.Invoice.PAID)

        name = self.request.GET.get('name')
        if name:
            queryset = queryset.filter(payments__name__icontains=name).distinct()

        invoices = list(queryset.order_by('closing_date'))
        for inv in invoices:
            inv.prefetched_payments = list(inv.payments.all().order_by('date_payment'))
        return invoices

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cards = models.CreditCard.objects.filter(user=self.request.user).select_related('bank')
        selected_card = self._selected_card()
        invoices = context.get('invoices', context.get('object_list', []))

        total_open = Decimal('0.00')
        total_closed = Decimal('0.00')
        total_paid = Decimal('0.00')
        for inv in invoices:
            if inv.status == models.Invoice.OPEN:
                total_open += inv.total
            elif inv.status == models.Invoice.CLOSED:
                total_closed += inv.total
            elif inv.status == models.Invoice.PAID:
                total_paid += inv.total

        credit_limit = Decimal('0.00')
        credit_used = Decimal('0.00')
        credit_available = Decimal('0.00')
        if selected_card:
            credit_limit = selected_card.credit_limit
            credit_used = models.Payment.objects.filter(
                user=self.request.user, card=selected_card, paid=False,
            ).aggregate(
                total=Coalesce(Sum('value'), Value(Decimal('0.00')))
            )['total']
            credit_available = max(credit_limit - credit_used, Decimal('0.00'))

        context['cards'] = cards
        context['selected_card'] = selected_card
        context['show_hidden'] = self._show_hidden()
        context['total_open'] = total_open
        context['total_closed'] = total_closed
        context['total_paid'] = total_paid
        context['credit_limit'] = credit_limit
        context['credit_used'] = credit_used
        context['credit_available'] = credit_available
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = models.Invoice
    template_name = 'invoice_detail.html'

    def get_queryset(self):
        return super().get_queryset().filter(card__user=self.request.user).select_related('card', 'card__bank')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payments'] = self.object.payments.all().order_by('date_payment')
        return context


class InvoicePayView(LoginRequiredMixin, View):
    def post(self, request, pk):
        invoice = get_object_or_404(models.Invoice, pk=pk, card__user=request.user)
        invoice = mark_invoice_paid(invoice)

        if not getattr(invoice, '_status_changed', False):
            return JsonResponse({'success': True, 'already_paid': True})
        return JsonResponse({'success': True})


class InvoiceUnpayView(LoginRequiredMixin, View):
    def post(self, request, pk):
        invoice = get_object_or_404(models.Invoice, pk=pk, card__user=request.user)
        invoice = mark_invoice_unpaid(invoice)

        if not getattr(invoice, '_status_changed', False):
            return JsonResponse({'success': True, 'already_unpaid': True})
        return JsonResponse({'success': True})
