from django.urls import path

from . import views


urlpatterns = [
    path('accounts/list/', views.AccountListView.as_view(), name='account_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/edit/', views.account_edit, name='account_edit'),
]
