from django.urls import path

from . import views


urlpatterns = [
    path('accounts/list/', views.AccountListView.as_view(), name='account_list'),
    path('accounts/edit/', views.account_edit, name='account_edit'),
    path('invite/<str:token>/', views.invite_accept, name='invite_accept'),
    path('mfa/setup/', views.mfa_setup, name='mfa_setup'),
    path('mfa/verify/', views.mfa_verify, name='mfa_verify'),
    path('accounts/password/', views.PasswordChangeView.as_view(), name='password_change'),
    path('accounts/password/done/', views.PasswordChangeDoneView.as_view(), name='password_change_done'),
]
