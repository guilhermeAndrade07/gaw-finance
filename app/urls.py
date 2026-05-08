from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/expenses-by-month/', views.get_expenses_by_month, name='get_expenses_by_month'),

    path('api/v1/', include('authentication.urls')),

    path('', include('banks.urls')),
    path('', include('categories.urls')),
    path('', include('inflows.urls')),
    path('', include('outflows.urls')),
    path('', include('payment.urls')),
    path('', include('signatures.urls')),
]
