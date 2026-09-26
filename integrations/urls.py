from django.urls import path

from integrations.views import whatsapp_webhook

app_name = 'integrations'

urlpatterns = [
    path('whatsapp/webhook/', whatsapp_webhook, name='whatsapp_webhook'),
]
