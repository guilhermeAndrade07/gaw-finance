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


class CustomReportView(LoginRequiredMixin, View):
    login_url = 'login'

    @staticmethod
    def _safe_int(value):
        if not value:
            return None
        try:
            return int(str(value).replace('.', '').replace(',', ''))
        except (ValueError, TypeError):
            return None

    def get(self, request):
        month = self._safe_int(request.GET.get('month'))
        year = self._safe_int(request.GET.get('year'))
        sections = request.GET.getlist('sections')

        buffer = services.generate_custom_report(request.user, sections, month, year)
        GeneratedReport.objects.create(user=request.user, report_type='custom')
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="relatorio_personalizado.pdf"'
        return response
