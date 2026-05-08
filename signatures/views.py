from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from rest_framework import generics
from app.mixins import UserScopedAPIMixin, UserScopedFormMixin, UserScopedQuerySetMixin
from .models import Signature
from .forms import SignatureForm
from .serializers import SignatureSerializer


class SignatureListView(LoginRequiredMixin, UserScopedQuerySetMixin, ListView):
    model = Signature
    template_name = 'signature_list.html'
    context_object_name = 'signatures'

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.GET.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Sum
        total_value = Signature.objects.filter(user=self.request.user, is_active=True).aggregate(Sum('value'))['value__sum'] or 0
        context['total_signatures_value'] = total_value
        return context


class SignatureCreateView(LoginRequiredMixin, UserScopedFormMixin, CreateView):
    model = Signature
    template_name = 'signature_create.html'
    form_class = SignatureForm
    success_url = reverse_lazy('signature_list')


class SignatureDetailView(LoginRequiredMixin, UserScopedQuerySetMixin, DetailView):
    model = Signature
    template_name = 'signature_detail.html'


class SignatureUpdateView(LoginRequiredMixin, UserScopedQuerySetMixin, UserScopedFormMixin, UpdateView):
    model = Signature
    template_name = 'signature_update.html'
    form_class = SignatureForm
    success_url = reverse_lazy('signature_list')


class SignatureDeleteView(LoginRequiredMixin, UserScopedQuerySetMixin, DeleteView):
    model = Signature
    template_name = 'signature_delete.html'
    success_url = reverse_lazy('signature_list')


class SignatureCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        signature = get_object_or_404(Signature, pk=pk, user=request.user)
        signature.is_active = False
        signature.save()
        return redirect('signature_list')


class SignatureCreateListAPIView(UserScopedAPIMixin, generics.ListCreateAPIView):
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer


class SignatureRetrieveUpdateDestroyAPIView(UserScopedAPIMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer
