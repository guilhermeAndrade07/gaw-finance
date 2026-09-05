from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.views.generic import DetailView, FormView, ListView
from rest_framework import generics

from app.mixins import UserScopedAPIMixin, UserScopedQuerySetMixin

from . import forms, models, serializers, services


class BankTransferListView(LoginRequiredMixin, UserScopedQuerySetMixin, ListView):
    model = models.BankTransfer
    template_name = 'transfer_list.html'
    context_object_name = 'transfers'

    def get_queryset(self):
        return super().get_queryset().select_related('source_bank', 'destination_bank')


class BankTransferCreateView(LoginRequiredMixin, FormView):
    template_name = 'transfer_create.html'
    form_class = forms.BankTransferForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            transfer = services.create_bank_transfer(
                user=self.request.user,
                title=form.cleaned_data.get('title'),
                source_bank=form.cleaned_data['source_bank'],
                destination_bank=form.cleaned_data['destination_bank'],
                value=form.cleaned_data['value'],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, 'Transferência entre bancos registrada com sucesso.')
        return redirect('transfer_detail', pk=transfer.pk)


class BankTransferDetailView(LoginRequiredMixin, UserScopedQuerySetMixin, DetailView):
    model = models.BankTransfer
    template_name = 'transfer_detail.html'
    context_object_name = 'transfer'

    def get_queryset(self):
        return super().get_queryset().select_related('source_bank', 'destination_bank')


class BankTransferCreateListAPIView(UserScopedAPIMixin, generics.ListCreateAPIView):
    queryset = models.BankTransfer.objects.all()
    serializer_class = serializers.BankTransferSerializer


class BankTransferRetrieveAPIView(UserScopedAPIMixin, generics.RetrieveAPIView):
    queryset = models.BankTransfer.objects.all()
    serializer_class = serializers.BankTransferSerializer
