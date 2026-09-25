from django.conf import settings
from django.db import models
from django.utils import timezone

from .context import request_id_var


def current_request_id():
    return request_id_var.get('')


class AuditEvent(models.Model):
    SUCCESS = 'success'
    FAILURE = 'failure'

    STATUS_CHOICES = [
        (SUCCESS, 'Sucesso'),
        (FAILURE, 'Falha'),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='audit_events',
        null=True,
        blank=True,
    )
    actor_username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=100, blank=True)
    resource_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SUCCESS)
    request_id = models.CharField(max_length=64, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', '-created_at'], name='audit_actor_created_idx'),
            models.Index(fields=['action', '-created_at'], name='audit_action_created_idx'),
            models.Index(fields=['resource_type', 'resource_id'], name='audit_resource_idx'),
        ]

    @staticmethod
    def user_snapshot(user):
        if user is None or not getattr(user, 'is_authenticated', False):
            return None, ''
        return user, user.get_username()

    def __str__(self):
        actor = self.actor_username or 'anonymous'
        return f'{self.action} - {self.resource_type}:{self.resource_id} - {actor}'
