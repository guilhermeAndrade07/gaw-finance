import calendar
from decimal import Decimal, ROUND_HALF_UP

from rest_framework import generics
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.db.models import Sum
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from app.mixins import UserScopedAPIMixin, UserScopedFormMixin, UserScopedQuerySetMixin
from . import models, forms, serializers


class PaymentListView(LoginRequiredMixin, UserScopedQuerySetMixin, ListView):
    model = models.Payment
    template_name = 'payment_list.html'
    context_object_name = 'payment'

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
        show_hidden = self._show_hidden()
        queryset = super().get_queryset().filter(paid=show_hidden)
        name = self.request.GET.get('name')
        month = self.request.GET.get('month')
        selected_card = self._selected_card()

        if not selected_card:
            return queryset.none()

        queryset = queryset.filter(card=selected_card)

        if name:
            queryset = queryset.filter(name__icontains=name)

        if month:
            try:
                queryset = queryset.filter(date_payment__month=int(month))
            except (ValueError, TypeError):
                pass

        return queryset.order_by('date_payment')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        show_hidden = self._show_hidden()
        listed_items = context.get('payment', context.get('object_list', []))
        cards = models.CreditCard.objects.filter(user=self.request.user).select_related('bank')
        selected_card = self._selected_card()

        if hasattr(listed_items, 'aggregate'):
            total = listed_items.aggregate(Sum('value'))['value__sum'] or 0
        else:
            total = sum((item.value or 0) for item in listed_items)

        credit_limit = Decimal('0.00')
        credit_used = Decimal('0.00')

        if selected_card:
            usage_queryset = models.Payment.objects.filter(user=self.request.user, paid=False)
            usage_queryset = usage_queryset.filter(card=selected_card)
            credit_limit = selected_card.credit_limit
            credit_used = usage_queryset.aggregate(
                total=Coalesce(Sum('value'), Value(Decimal('0.00')))
            )['total']
        credit_available = max(credit_limit - credit_used, Decimal('0.00'))

        context['payment_total'] = total
        context['show_hidden'] = show_hidden
        context['cards'] = cards
        context['selected_card'] = selected_card
        context['credit_used'] = credit_used
        context['credit_available'] = credit_available
        context['months'] = [
            ('1', 'Janeiro'),
            ('2', 'Fevereiro'),
            ('3', 'Marco'),
            ('4', 'Abril'),
            ('5', 'Maio'),
            ('6', 'Junho'),
            ('7', 'Julho'),
            ('8', 'Agosto'),
            ('9', 'Setembro'),
            ('10', 'Outubro'),
            ('11', 'Novembro'),
            ('12', 'Dezembro'),
        ]
        return context


class PaymentCreateView(LoginRequiredMixin, UserScopedFormMixin, CreateView):
    model = models.Payment
    template_name = 'payment_create.html'
    form_class = forms.PaymentForm
    success_url = reverse_lazy('payment_list')

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

    @staticmethod
    def _add_months(base_date, months):
        month = base_date.month - 1 + months
        year = base_date.year + month // 12
        month = month % 12 + 1
        day = min(base_date.day, calendar.monthrange(year, month)[1])
        return base_date.replace(year=year, month=month, day=day)

    def form_valid(self, form):
        parcelas = form.cleaned_data.get('parcelas') or 1

        if parcelas == 1:
            return super().form_valid(form)

        name = form.cleaned_data.get('name')
        description = form.cleaned_data.get('description')
        category = form.cleaned_data.get('category')
        card = form.cleaned_data.get('card')
        date_payment = form.cleaned_data.get('date_payment')
        total_value = form.cleaned_data.get('value')

        payments_to_create = []
        installment_value = None

        if total_value is not None:
            installment_value = (Decimal(total_value) / Decimal(parcelas)).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP,
            )

        accumulated = Decimal('0.00')

        for installment_index in range(parcelas):
            current_value = total_value

            if installment_value is not None:
                if installment_index < parcelas - 1:
                    current_value = installment_value
                    accumulated += installment_value
                else:
                    current_value = (Decimal(total_value) - accumulated).quantize(
                        Decimal('0.01'),
                        rounding=ROUND_HALF_UP,
                    )

            current_date = (
                self._add_months(date_payment, installment_index)
                if date_payment is not None
                else None
            )

            payments_to_create.append(
                models.Payment(
                    user=self.request.user,
                    name=f'{name} ({installment_index + 1}/{parcelas})',
                    description=description,
                    category=category,
                    card=card,
                    date_payment=current_date,
                    value=current_value,
                    parcelas=parcelas,
                )
            )

        models.Payment.objects.bulk_create(payments_to_create)
        if card:
            return HttpResponseRedirect(f'{self.success_url}?card={card.id}')

        return HttpResponseRedirect(str(self.success_url))


class PaymentDetailView(LoginRequiredMixin, UserScopedQuerySetMixin, DetailView):
    model = models.Payment
    template_name = 'payment_detail.html'


class PaymentUpdateView(LoginRequiredMixin, UserScopedQuerySetMixin, UserScopedFormMixin, UpdateView):
    model = models.Payment
    template_name = 'payment_update.html'
    form_class = forms.PaymentForm
    success_url = reverse_lazy('payment_list')


class PaymentDeleteView(LoginRequiredMixin, UserScopedQuerySetMixin, DeleteView):
    model = models.Payment
    template_name = 'payment_delete.html'
    success_url = reverse_lazy('payment_list')


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
        payment = get_object_or_404(models.Payment, pk=pk, user=request.user)

        if payment.paid:
            return JsonResponse({'success': True, 'already_paid': True})

        payment.paid = True
        payment.save(update_fields=['paid', 'update_at'])
        return JsonResponse({'success': True})


class PaymentMarkAsUnpaidView(LoginRequiredMixin, View):
    def post(self, request, pk):
        payment = get_object_or_404(models.Payment, pk=pk, user=request.user)

        if not payment.paid:
            return JsonResponse({'success': True, 'already_unpaid': True})

        payment.paid = False
        payment.save(update_fields=['paid', 'update_at'])
        return JsonResponse({'success': True})
