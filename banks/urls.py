from django.urls import path
from . import views


urlpatterns = [
    path('banks/list/', views.BankListView.as_view(), name='bank_list'),
    path('banks/create/', views.BankCreateView.as_view(), name='bank_create'),
    path('banks/<int:pk>/detail/', views.BankDetailView.as_view(), name='bank_detail'),
    path('banks/<int:pk>/update/', views.BankUpdateView.as_view(), name='bank_update'),
    path('banks/<int:pk>/delete/', views.BankDeleteView.as_view(), name='bank_delete'),

    path('api/v1/banks/', views.BankCreateListAPIView.as_view(), name='bank-create-list-api-view'),
    path('api/v1/banks/<int:pk>/', views.BankRetriveUpdateDestroyAPIView.as_view(), name='bank-detail-api-view'),
]
