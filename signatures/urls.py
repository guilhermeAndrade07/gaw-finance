from django.urls import path
from . import views


urlpatterns = [
    path('signature/list/', views.SignatureListView.as_view(), name='signature_list'),
    path('signature/create/', views.SignatureCreateView.as_view(), name='signature_create'),
    path('signature/<int:pk>/detail/', views.SignatureDetailView.as_view(), name='signature_detail'),
    path('signature/<int:pk>/update/', views.SignatureUpdateView.as_view(), name='signature_update'),
    path('signature/<int:pk>/delete/', views.SignatureDeleteView.as_view(), name='signature_delete'),
    path('signature/<int:pk>/cancel/', views.SignatureCancelView.as_view(), name='signature_cancel'),
    
    path('api/v1/signatures/', views.SignatureCreateListAPIView.as_view(), name='signature-create-list-api-view'),
    path('api/v1/signatures/<int:pk>/', views.SignatureRetrieveUpdateDestroyAPIView.as_view(), name='signature-detail-api-view'),
]
