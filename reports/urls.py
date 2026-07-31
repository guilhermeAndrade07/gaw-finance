from django.urls import path

from . import views


urlpatterns = [
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('reports/custom/', views.CustomReportView.as_view(), name='report_custom'),
]
