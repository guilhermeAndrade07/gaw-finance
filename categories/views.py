from rest_framework import generics
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from app.mixins import UserScopedAPIMixin, UserScopedFormMixin, UserScopedQuerySetMixin
from . import models, forms, serializers


class CategoryListView(LoginRequiredMixin, UserScopedQuerySetMixin, ListView):
    model = models.Category
    template_name = 'category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.GET.get('name')

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class CategoryCreateView(LoginRequiredMixin, UserScopedFormMixin, CreateView):
    model = models.Category
    template_name = 'category_create.html'
    form_class = forms.CategoryForm
    success_url = reverse_lazy('category_list')


class CategoryDetailView(LoginRequiredMixin, UserScopedQuerySetMixin, DetailView):
    model = models.Category
    template_name = 'category_detail.html'


class CategoryUpdateView(LoginRequiredMixin, UserScopedQuerySetMixin, UserScopedFormMixin, UpdateView):
    model = models.Category
    template_name = 'category_update.html'
    form_class = forms.CategoryForm
    success_url = reverse_lazy('category_list')


class CategoryDeleteView(LoginRequiredMixin, UserScopedQuerySetMixin, DeleteView):
    model = models.Category
    template_name = 'category_delete.html'
    success_url = reverse_lazy('category_list')


class CategoryCreateListAPIView(UserScopedAPIMixin, generics.ListCreateAPIView):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer


class CategoryRetriveUpdateDestroyAPIView(UserScopedAPIMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer
