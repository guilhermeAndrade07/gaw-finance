from django.urls import path

from . import views


urlpatterns = [
    path('investments/list/', views.InvestmentListView.as_view(), name='investment_list'),
    path('investments/create/', views.InvestmentCreateView.as_view(), name='investment_create'),
    path('investments/<int:pk>/detail/', views.InvestmentDetailView.as_view(), name='investment_detail'),
    path('investments/<int:pk>/update/', views.InvestmentUpdateView.as_view(), name='investment_update'),
    path('investments/<int:pk>/delete/', views.InvestmentDeleteView.as_view(), name='investment_delete'),
    path('investments/movements/create/', views.InvestmentMovementCreateView.as_view(), name='investment_movement_create'),

    path('api/v1/investments/', views.InvestmentAssetCreateListAPIView.as_view(), name='investment-create-list-api-view'),
    path('api/v1/investments/<int:pk>/', views.InvestmentAssetRetrieveUpdateDestroyAPIView.as_view(), name='investment-detail-api-view'),
    path('api/v1/investment-movements/', views.InvestmentMovementCreateListAPIView.as_view(), name='investment-movement-create-list-api-view'),
    path('api/v1/investment-movements/<int:pk>/', views.InvestmentMovementRetrieveAPIView.as_view(), name='investment-movement-detail-api-view'),
]
