from django.urls import path

from . import views


urlpatterns = [
    path('transfers/list/', views.BankTransferListView.as_view(), name='transfer_list'),
    path('transfers/create/', views.BankTransferCreateView.as_view(), name='transfer_create'),
    path('transfers/<int:pk>/detail/', views.BankTransferDetailView.as_view(), name='transfer_detail'),

    path('api/v1/transfers/', views.BankTransferCreateListAPIView.as_view(), name='transfer-create-list-api-view'),
    path('api/v1/transfers/<int:pk>/', views.BankTransferRetrieveAPIView.as_view(), name='transfer-detail-api-view'),
]
