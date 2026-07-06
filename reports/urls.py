from django.urls import path

from . import views


urlpatterns = [
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('reports/cash-flow/', views.CashFlowReportView.as_view(), name='report_cash_flow'),
    path('reports/expenses-by-category/', views.ExpensesByCategoryReportView.as_view(), name='report_expenses_by_category'),
    path('reports/investments/', views.InvestmentsReportView.as_view(), name='report_investments'),
]
