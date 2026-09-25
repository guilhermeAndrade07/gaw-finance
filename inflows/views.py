from datetime import date

from rest_framework import generics
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from app.mixins import UserScopedAPIMixin, UserScopedFormMixin, UserScopedQuerySetMixin
from . import models, forms, serializers
from .services import register_inflow


class InflowListView(LoginRequiredMixin, UserScopedQuerySetMixin, ListView):

    model = models.Inflow
    template_name = 'inflow_list.html'
    context_object_name = 'inflows'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        title = self.request.GET.get('title')
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')

        if title:
            queryset = queryset.filter(title__icontains=title)

        if month:
            try:
                queryset = queryset.filter(created_at__month=int(month))
            except (ValueError, TypeError):
                pass

        if year:
            try:
                queryset = queryset.filter(created_at__year=int(year))
            except (ValueError, TypeError):
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        context['years'] = range(date.today().year - 4, date.today().year + 1)
        return context


class InflowCreateView(LoginRequiredMixin, UserScopedFormMixin, CreateView):
    model = models.Inflow
    template_name = 'inflow_create.html'
    form_class = forms.InflowForm
    success_url = reverse_lazy('inflow_list')

    def form_valid(self, form):
        try:
            self.object = register_inflow(
                user=self.request.user,
                bank=form.cleaned_data['bank'],
                value=form.cleaned_data['value'],
                title=form.cleaned_data.get('title'),
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())


class InflowDetailView(LoginRequiredMixin, UserScopedQuerySetMixin, DetailView):

    model = models.Inflow
    template_name = 'inflow_detail.html'


class InflowCreateListAPIView(UserScopedAPIMixin, generics.ListCreateAPIView):
    queryset = models.Inflow.objects.all()
    serializer_class = serializers.InflowSerializer


class InflowRetriveAPIView(UserScopedAPIMixin, generics.RetrieveAPIView):
    queryset = models.Inflow.objects.all()
    serializer_class = serializers.InflowSerializer
