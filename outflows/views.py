from rest_framework import generics
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from . import models, forms, serializers
from categories.models import Category


class OutflowListView(LoginRequiredMixin, ListView):
    model = models.Outflow
    template_name = 'outflow_list.html'
    context_object_name = 'outflows'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        title = self.request.GET.get('title')
        category = self.request.GET.get('category')
        month = self.request.GET.get('month')

        if title:
            queryset = queryset.filter(title__icontains=title)

        if category:
            queryset = queryset.filter(category__id=category)

        if month:
            try:
                queryset = queryset.filter(created_at__month=int(month))
            except (ValueError, TypeError):
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
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


class OutflowCreateView(LoginRequiredMixin, CreateView):
    model = models.Outflow
    template_name = 'outflow_create.html'
    form_class = forms.OutflowForm
    success_url = reverse_lazy('outflow_list')


class OutflowDetailView(LoginRequiredMixin, DetailView):
    model = models.Outflow
    template_name = 'outflow_detail.html'


class OutflowCreateListAPIView(generics.ListCreateAPIView):
    queryset = models.Outflow.objects.all()
    serializer_class = serializers.OutflowSerializer


class OutflowRetriveAPIView(generics.RetrieveAPIView):
    queryset = models.Outflow.objects.all()
    serializer_class = serializers.OutflowSerializer
