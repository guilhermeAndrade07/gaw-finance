from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.edit import FormView
from rest_framework import generics

from app.mixins import UserScopedAPIMixin, UserScopedFormMixin, UserScopedQuerySetMixin

from . import forms, models, serializers, services


class InvestmentListView(LoginRequiredMixin, UserScopedQuerySetMixin, ListView):
    model = models.InvestmentAsset
    template_name = 'investment_list.html'
    context_object_name = 'assets'

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.GET.get('name')
        asset_type = self.request.GET.get('asset_type')

        if name:
            queryset = queryset.filter(name__icontains=name)
        if asset_type:
            queryset = queryset.filter(asset_type=asset_type)

        return queryset.select_related('bank')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assets = list(context['assets'])
        grouped_assets = []

        for value, label in models.InvestmentAsset.ASSET_TYPE_CHOICES:
            items = [asset for asset in assets if asset.asset_type == value]
            if not items:
                continue

            grouped_assets.append({
                'value': value,
                'label': label,
                'items': items,
                'total': sum(asset.current_value for asset in items),
            })

        total_current_value = sum(asset.current_value for asset in assets)
        context['grouped_assets'] = grouped_assets
        context['total_current_value'] = total_current_value
        context['active_assets_count'] = len([asset for asset in assets if asset.is_active])
        context['asset_types'] = models.InvestmentAsset.ASSET_TYPE_CHOICES
        return context


class InvestmentCreateView(LoginRequiredMixin, CreateView):
    model = models.InvestmentAsset
    template_name = 'investment_create.html'
    form_class = forms.InvestmentAssetForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        initial_amount = form.cleaned_data.get('initial_amount')
        initial_date = form.cleaned_data.get('initial_date')
        register_cash_flow = form.cleaned_data.get('register_cash_flow')
        manual_current_value = form.cleaned_data.get('current_value')
        raw_current_value = str(form.data.get('current_value', '')).strip()
        manual_current_value_provided = raw_current_value != ''

        if initial_amount and manual_current_value in (None, 0):
            manual_current_value_provided = False

        asset = form.save(commit=False)
        asset.user = self.request.user
        asset.current_value = 0

        try:
            from django.db import transaction

            with transaction.atomic():
                asset.save()
                self.object = asset

                if initial_amount and initial_amount > 0:
                    services.register_investment_movement(
                        user=self.request.user,
                        asset=asset,
                        operation_type=models.InvestmentMovement.APPORTION,
                        value=initial_amount,
                        movement_date=initial_date,
                        register_cash_flow=register_cash_flow,
                        notes='Aporte inicial do ativo',
                    )

                if manual_current_value_provided:
                    asset.current_value = manual_current_value or 0
                    asset.save(update_fields=['current_value', 'update_at'])
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, 'Ativo de investimento criado com sucesso.')
        return redirect('investment_detail', pk=self.object.pk)


class InvestmentDetailView(LoginRequiredMixin, UserScopedQuerySetMixin, DetailView):
    model = models.InvestmentAsset
    template_name = 'investment_detail.html'
    context_object_name = 'asset'

    def get_queryset(self):
        return super().get_queryset().select_related('bank')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.object
        movements = asset.movements.all()
        total_applied = movements.filter(operation_type=models.InvestmentMovement.APPORTION).aggregate(Sum('value'))['value__sum'] or 0
        total_redeemed = movements.filter(operation_type=models.InvestmentMovement.REDEMPTION).aggregate(Sum('value'))['value__sum'] or 0
        net_applied = total_applied - total_redeemed
        context['movements'] = movements
        context['total_applied'] = total_applied
        context['total_redeemed'] = total_redeemed
        context['net_applied'] = net_applied
        context['profit_loss'] = asset.current_value - net_applied
        return context


class InvestmentUpdateView(LoginRequiredMixin, UserScopedQuerySetMixin, UserScopedFormMixin, UpdateView):
    model = models.InvestmentAsset
    template_name = 'investment_update.html'
    form_class = forms.InvestmentAssetForm

    def get_success_url(self):
        return reverse('investment_detail', kwargs={'pk': self.object.pk})


class InvestmentDeleteView(LoginRequiredMixin, UserScopedQuerySetMixin, DeleteView):
    model = models.InvestmentAsset
    template_name = 'investment_delete.html'
    success_url = reverse_lazy('investment_list')


class InvestmentMovementCreateView(LoginRequiredMixin, FormView):
    template_name = 'investment_movement_create.html'
    form_class = forms.InvestmentMovementForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['initial_asset'] = self.request.GET.get('asset')
        return kwargs

    def form_valid(self, form):
        asset = form.cleaned_data['asset']

        try:
            services.register_investment_movement(
                user=self.request.user,
                asset=asset,
                operation_type=form.cleaned_data['operation_type'],
                value=form.cleaned_data['value'],
                movement_date=form.cleaned_data['movement_date'],
                register_cash_flow=form.cleaned_data['register_cash_flow'],
                notes=form.cleaned_data.get('notes', ''),
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, 'Movimentacao registrada com sucesso.')
        return HttpResponseRedirect(reverse('investment_detail', kwargs={'pk': asset.pk}))


class InvestmentAssetCreateListAPIView(UserScopedAPIMixin, generics.ListCreateAPIView):
    queryset = models.InvestmentAsset.objects.all()
    serializer_class = serializers.InvestmentAssetSerializer


class InvestmentAssetRetrieveUpdateDestroyAPIView(UserScopedAPIMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = models.InvestmentAsset.objects.all()
    serializer_class = serializers.InvestmentAssetSerializer


class InvestmentMovementCreateListAPIView(UserScopedAPIMixin, generics.ListAPIView):
    queryset = models.InvestmentMovement.objects.all()
    serializer_class = serializers.InvestmentMovementSerializer


class InvestmentMovementRetrieveAPIView(UserScopedAPIMixin, generics.RetrieveAPIView):
    queryset = models.InvestmentMovement.objects.all()
    serializer_class = serializers.InvestmentMovementSerializer
