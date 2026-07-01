from django.urls import path
from . import views


urlpatterns = [
    path('credit-cards/list/', views.CreditCardListView.as_view(), name='credit_card_list'),
    path('credit-cards/create/', views.CreditCardCreateView.as_view(), name='credit_card_create'),
    path('credit-cards/<int:pk>/detail/', views.CreditCardDetailView.as_view(), name='credit_card_detail'),
    path('credit-cards/<int:pk>/update/', views.CreditCardUpdateView.as_view(), name='credit_card_update'),
    path('credit-cards/<int:pk>/delete/', views.CreditCardDeleteView.as_view(), name='credit_card_delete'),

    path('payment/list/', views.PaymentListView.as_view(), name='payment_list'),
    path('payment/<int:pk>/mark-paid/', views.PaymentMarkAsPaidView.as_view(), name='payment_mark_paid'),
    path('payment/<int:pk>/mark-unpaid/', views.PaymentMarkAsUnpaidView.as_view(), name='payment_mark_unpaid'),
    path('payment/create/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('payment/<int:pk>/detail/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('payment/<int:pk>/update/', views.PaymentUpdateView.as_view(), name='payment_update'),
    path('payment/<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),

    path('api/v1/payment/', views.PaymentCreateListAPIView.as_view(), name='payment-create-list-api-view'),
    path('api/v1/payment/<int:pk>/', views.PaymentRetriveUpdateDestroyAPIView.as_view(), name='payment-detail-api-view'),
]
