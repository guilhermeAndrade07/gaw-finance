import json
import logging

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from auditing.context import request_id_var
from auditing.logging import JSONFormatter
from auditing.models import AuditEvent
from auditing.services import record_audit_event


class AuditEventTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='audit-user',
            email='audit-user@gawfinance.com',
            password='senha-forte-123',
        )

    def test_record_audit_event_with_request_context(self):
        request = RequestFactory().post(
            '/login/',
            HTTP_USER_AGENT='Mozilla/5.0',
            REMOTE_ADDR='203.0.113.10',
            HTTP_X_REQUEST_ID='fixed-request-id',
        )
        request_id_var.set('fixed-request-id')

        event = record_audit_event(
            action='auth.login.success',
            user=self.user,
            resource_type='User',
            resource_id=self.user.pk,
            description='Login realizado.',
            request=request,
        )

        self.assertEqual(event.action, 'auth.login.success')
        self.assertEqual(event.actor, self.user)
        self.assertEqual(event.resource_type, 'User')
        self.assertEqual(event.resource_id, str(self.user.pk))
        self.assertEqual(event.request_id, 'fixed-request-id')
        self.assertEqual(event.ip_address, '203.0.113.10')
        self.assertEqual(event.user_agent, 'Mozilla/5.0')
        self.assertEqual(event.status, AuditEvent.SUCCESS)
        self.assertTrue(AuditEvent.objects.filter(pk=event.pk).exists())

    def test_record_audit_event_failure_does_not_break_operation(self):
        event = record_audit_event(
            action='finance.outflow.create',
            user=self.user,
            resource_type='Outflow',
            resource_id='42',
            status=AuditEvent.FAILURE,
            metadata={'reason': 'saldo insuficiente'},
        )

        self.assertEqual(event.status, AuditEvent.FAILURE)
        self.assertEqual(event.metadata, {'reason': 'saldo insuficiente'})


class RequestIDMiddlewareTests(TestCase):
    def test_request_id_is_generated_and_returned(self):
        response = self.client.get(reverse('health_check'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('X-Request-ID', response.headers)
        self.assertEqual(len(response.headers['X-Request-ID']), 32)

    def test_request_id_from_header_is_preserved(self):
        response = self.client.get(
            reverse('health_check'),
            headers={'X-Request-ID': 'fixed-request-id'},
        )

        self.assertEqual(response.headers.get('X-Request-ID'), 'fixed-request-id')


class JSONFormatterTests(TestCase):
    def test_formatter_outputs_json_with_request_id(self):
        formatter = JSONFormatter()
        request_id_var.set('test-request-id')
        record = logging.LogRecord(
            name='gaw_finance',
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg='Evento de teste',
            args=(),
            exc_info=None,
        )

        payload = json.loads(formatter.format(record))

        self.assertEqual(payload['message'], 'Evento de teste')
        self.assertEqual(payload['level'], 'INFO')
        self.assertEqual(payload['request_id'], 'test-request-id')


class PruneAuditEventsTests(TestCase):
    def test_prune_audit_events_removes_old_events_only(self):
        from datetime import timedelta

        from django.core.management import call_command
        from django.utils import timezone

        old_user = User.objects.create_user(username='old-audit-user', password='pass123')
        current_user = User.objects.create_user(username='current-audit-user', password='pass123')

        old_event = AuditEvent.objects.create(
            actor=old_user,
            actor_username=old_user.username,
            action='old.event',
            created_at=timezone.now() - timedelta(days=31),
        )
        current_event = AuditEvent.objects.create(
            actor=current_user,
            actor_username=current_user.username,
            action='current.event',
            created_at=timezone.now(),
        )

        call_command('prune_audit_events', days=30)

        self.assertFalse(AuditEvent.objects.filter(pk=old_event.pk).exists())
        self.assertTrue(AuditEvent.objects.filter(pk=current_event.pk).exists())
