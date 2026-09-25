from django.urls import path

from .views import (
    ThrottledTokenObtainPairView,
    ThrottledTokenRefreshView,
    ThrottledTokenVerifyView,
    TokenLogoutView,
)


urlpatterns = [
    path('authentication/token/', ThrottledTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('authentication/token/refresh/', ThrottledTokenRefreshView.as_view(), name='token_refresh'),
    path('authentication/token/verify/', ThrottledTokenVerifyView.as_view(), name='token_verify'),
    path('authentication/token/logout/', TokenLogoutView.as_view(), name='token_logout'),
]
