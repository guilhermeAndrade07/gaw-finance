from rest_framework import generics
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from app.mixins import UserScopedAPIMixin, UserScopedFormMixin, UserScopedQuerySetMixin
from . import models, forms, serializers


class InflowListView(LoginRequiredMixin, UserScopedQuerySetMixin, ListView):
    model = models.Inflow
    template_name = 'inflow_list.html'
    context_object_name = 'inflows'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        title = self.request.GET.get('title')
        month = self.request.GET.get('month')

        if title:
            queryset = queryset.filter(title__icontains=title)

        if month:
            try:
                queryset = queryset.filter(created_at__month=int(month))
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
        return context


class InflowCreateView(LoginRequiredMixin, UserScopedFormMixin, CreateView):
    model = models.Inflow
    template_name = 'inflow_create.html'
    form_class = forms.InflowForm
    success_url = reverse_lazy('inflow_list')


class InflowDetailView(LoginRequiredMixin, UserScopedQuerySetMixin, DetailView):
    model = models.Inflow
    template_name = 'inflow_detail.html'


class InflowCreateListAPIView(UserScopedAPIMixin, generics.ListCreateAPIView):
    queryset = models.Inflow.objects.all()
    serializer_class = serializers.InflowSerializer


class InflowRetriveAPIView(UserScopedAPIMixin, generics.RetrieveAPIView):
    queryset = models.Inflow.objects.all()
    serializer_class = serializers.InflowSerializer
