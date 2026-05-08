from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from rest_framework import generics
from .models import Signature
from .forms import SignatureForm
from .serializers import SignatureSerializer
from .services import generate_signature_outflows


class SignatureListView(LoginRequiredMixin, ListView):
    model = Signature
    template_name = 'signature_list.html'
    context_object_name = 'signatures'

    def get_queryset(self):
        # Trigger generation before listing
        generate_signature_outflows()
        
        queryset = super().get_queryset()
        name = self.request.GET.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class SignatureCreateView(LoginRequiredMixin, CreateView):
    model = Signature
    template_name = 'signature_create.html'
    form_class = SignatureForm
    success_url = reverse_lazy('signature_list')


class SignatureDetailView(LoginRequiredMixin, DetailView):
    model = Signature
    template_name = 'signature_detail.html'


class SignatureUpdateView(LoginRequiredMixin, UpdateView):
    model = Signature
    template_name = 'signature_update.html'
    form_class = SignatureForm
    success_url = reverse_lazy('signature_list')


class SignatureDeleteView(LoginRequiredMixin, DeleteView):
    model = Signature
    template_name = 'signature_delete.html'
    success_url = reverse_lazy('signature_list')


class SignatureCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        signature = get_object_or_404(Signature, pk=pk)
        signature.is_active = False
        signature.save()
        return redirect('signature_list')


class SignatureCreateListAPIView(generics.ListCreateAPIView):
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer


class SignatureRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer
