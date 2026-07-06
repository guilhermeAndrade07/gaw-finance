from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from app.metrics import get_months_list
from .models import GeneratedReport
from . import services


class ReportListView(LoginRequiredMixin, View):
    login_url = 'login'
    template_name = 'report_list.html'

    def get(self, request):
        from datetime import date
        current_year = date.today().year
        years_list = list(range(current_year - 2, current_year + 1))
        context = {
            'months_list': get_months_list(),
            'years_list': years_list,
        }
        return render(request, self.template_name, context)


class CashFlowReportView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        month = request.GET.get('month')
        year = request.GET.get('year')
        month = int(month) if month else None
        year = int(year) if year else None

        buffer = services.generate_cash_flow_report(request.user, month, year)
        GeneratedReport.objects.create(user=request.user, report_type='cash_flow')
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="fluxo_de_caixa.pdf"'
        return response


class ExpensesByCategoryReportView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        month = request.GET.get('month')
        year = request.GET.get('year')
        month = int(month) if month else None
        year = int(year) if year else None

        buffer = services.generate_expenses_by_category_report(request.user, month, year)
        GeneratedReport.objects.create(user=request.user, report_type='expenses_by_category')
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="despesas_por_categoria.pdf"'
        return response


class InvestmentsReportView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        buffer = services.generate_investments_report(request.user)
        GeneratedReport.objects.create(user=request.user, report_type='investments')
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="investimentos.pdf"'
        return response
