from django.contrib.auth.models import User
from django.db import models


class WhatsAppBinding(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='whatsapp_bindings')
    phone = models.CharField(max_length=20, unique=True)
    instance_name = models.CharField(max_length=100, default='gaw-finance')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['phone']
        verbose_name = 'Vinculo WhatsApp'
        verbose_name_plural = 'Vinculos WhatsApp'

    def __str__(self):
        return f'{self.phone} -> {self.user.username}'


class WhatsAppMessageLog(models.Model):

    STATUS_PENDING = 'pending'
    STATUS_PROCESSED = 'processed'
    STATUS_ERROR = 'error'
    STATUS_IGNORED = 'ignored'

    DIRECTION_IN = 'in'
    DIRECTION_OUT = 'out'

    binding = models.ForeignKey(
        WhatsAppBinding,
        on_delete=models.SET_NULL,
        related_name='message_logs',
        null=True,
        blank=True,
    )
    message_id = models.CharField(max_length=128, unique=True)
    direction = models.CharField(max_length=3, choices=[(DIRECTION_IN, 'Entrada'), (DIRECTION_OUT, 'Saida')])
    phone = models.CharField(max_length=20)
    raw_body = models.JSONField(null=True, blank=True)
    message_text = models.TextField(null=True, blank=True)
    interpreted_intent = models.CharField(max_length=20, null=True, blank=True)
    result_status = models.CharField(max_length=20, default=STATUS_PENDING)
    response_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Log de mensagem WhatsApp'
        verbose_name_plural = 'Logs de mensagens WhatsApp'

    def __str__(self):
        return f'{self.phone} ({self.direction}) {self.message_id[:12]}'
