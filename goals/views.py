import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from rest_framework import generics

from app.mixins import UserScopedAPIMixin, UserScopedFormMixin, UserScopedQuerySetMixin
from app import metrics

from . import models, forms, serializers


class MonthlyGoalListView(LoginRequiredMixin, UserScopedQuerySetMixin, ListView):
    model = models.MonthlyGoal
    template_name = 'goal_list.html'
    context_object_name = 'goals'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')

        if month:
            try:
                queryset = queryset.filter(month=int(month))
            except (ValueError, TypeError):
                pass
        if year:
            try:
                queryset = queryset.filter(year=int(year))
            except (ValueError, TypeError):
                pass

        return queryset.select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['months'] = [
            (i, name) for i, name in models.MONTHS_PT_BR.items()
        ]
        context['years'] = range(date.today().year - 2, date.today().year + 3)
        return context


class MonthlyGoalCreateView(LoginRequiredMixin, UserScopedFormMixin, CreateView):
    model = models.MonthlyGoal
    template_name = 'goal_form.html'
    form_class = forms.MonthlyGoalForm
    success_url = reverse_lazy('goal_list')

    def get_initial(self):
        initial = super().get_initial()
        today = date.today()
        initial.setdefault('month', today.month)
        initial.setdefault('year', today.year)
        return initial


class MonthlyGoalUpdateView(LoginRequiredMixin, UserScopedQuerySetMixin, UserScopedFormMixin, UpdateView):
    model = models.MonthlyGoal
    template_name = 'goal_form.html'
    form_class = forms.MonthlyGoalForm
    success_url = reverse_lazy('goal_list')


class MonthlyGoalDeleteView(LoginRequiredMixin, UserScopedQuerySetMixin, DeleteView):
    model = models.MonthlyGoal
    template_name = 'goal_confirm_delete.html'
    success_url = reverse_lazy('goal_list')


class MonthlyGoalDashboardView(LoginRequiredMixin, ListView):
    model = models.MonthlyGoal
    template_name = 'goal_dashboard.html'
    context_object_name = 'goals'

    def _resolve_period(self):
        today = date.today()
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')
        try:
            month = int(month) if month else today.month
        except (ValueError, TypeError):
            month = today.month
        try:
            year = int(year) if year else today.year
        except (ValueError, TypeError):
            year = today.year
        return month, year

    def get_queryset(self):
        month, year = self._resolve_period()
        return models.MonthlyGoal.objects.filter(
            user=self.request.user, month=month, year=year,
        ).select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        month, year = self._resolve_period()
        progress = metrics.get_goal_progress(self.request.user, month, year)
        context.update({
            'goals_progress': progress,
            'months_list': metrics.get_months_list(),
            'selected_month': month,
            'selected_year': year,
            'period_label': f'{models.MONTHS_PT_BR.get(month, month)} de {year}',
        })
        return context


class MonthlyGoalCreateListAPIView(UserScopedAPIMixin, generics.ListCreateAPIView):
    queryset = models.MonthlyGoal.objects.all()
    serializer_class = serializers.MonthlyGoalSerializer


class MonthlyGoalRetrieveUpdateDestroyAPIView(UserScopedAPIMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = models.MonthlyGoal.objects.all()
    serializer_class = serializers.MonthlyGoalSerializer


@login_required(login_url='login')
def get_goal_progress(request):
    month = request.GET.get('month')
    year = request.GET.get('year')

    if not month or not year:
        return JsonResponse({'error': 'Mes e ano sao obrigatorios'}, status=400)

    try:
        progress = metrics.get_goal_progress(request.user, int(month), int(year))
        return JsonResponse({
            'labels': json.loads(progress['labels']),
            'percentages': json.loads(progress['percentages']),
            'spent': json.loads(progress['spent']),
            'goals': json.loads(progress['goals']),
            'success': True,
        })
    except Exception:
        import logging
        logging.getLogger(__name__).exception('Erro ao buscar progresso das metas')
        return JsonResponse({'error': 'Erro ao processar os dados.', 'success': False}, status=500)
