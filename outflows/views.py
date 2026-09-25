from datetime import date

from rest_framework import generics
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from app.mixins import UserScopedAPIMixin, UserScopedFormMixin, UserScopedQuerySetMixin
from . import models, forms, serializers
from .services import register_outflow
from categories.models import Category


class OutflowListView(LoginRequiredMixin, UserScopedQuerySetMixin, ListView):

    model = models.Outflow
    template_name = 'outflow_list.html'
    context_object_name = 'outflows'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        title = self.request.GET.get('title')
        category = self.request.GET.get('category')
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')

        if title:
            queryset = queryset.filter(title__icontains=title)

        if category:
            queryset = queryset.filter(category__id=category)

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
        context['categories'] = Category.objects.filter(user=self.request.user)
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


class OutflowCreateView(LoginRequiredMixin, UserScopedFormMixin, CreateView):
    model = models.Outflow
    template_name = 'outflow_create.html'
    form_class = forms.OutflowForm
    success_url = reverse_lazy('outflow_list')

    def form_valid(self, form):
        try:
            self.object = register_outflow(
                user=self.request.user,
                bank=form.cleaned_data['bank'],
                value=form.cleaned_data['value'],
                title=form.cleaned_data.get('title'),
                category=form.cleaned_data.get('category'),
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())


class OutflowDetailView(LoginRequiredMixin, UserScopedQuerySetMixin, DetailView):

    model = models.Outflow
    template_name = 'outflow_detail.html'


class OutflowCreateListAPIView(UserScopedAPIMixin, generics.ListCreateAPIView):
    queryset = models.Outflow.objects.all()
    serializer_class = serializers.OutflowSerializer


class OutflowRetriveAPIView(UserScopedAPIMixin, generics.RetrieveAPIView):
    queryset = models.Outflow.objects.all()
    serializer_class = serializers.OutflowSerializer
