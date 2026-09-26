from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from banks.models import Bank
from categories.models import Category
from integrations.handlers import (
    handle_inflow,
    handle_outflow,
    handle_query,
)
from integrations.models import WhatsAppBinding, WhatsAppMessageLog
from integrations.resolvers import resolve_bank, resolve_category
from outflows.models import Outflow


def make_user(username='gaw'):
    return User.objects.create_user(username=username, password='testpass123')


def make_bank(user, name='Nubank'):
    return Bank.objects.create(
        user=user,
        name=name,
        account_type='corrente',
        agency=1,
        account=1,
        initial_balance=Decimal('1000.00'),
        balance=Decimal('1000.00'),
    )


class ResolverTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.other = make_user('other')
        self.bank = make_bank(self.user, 'Nubank')
        make_bank(self.other, 'Inter')
        self.category = Category.objects.create(user=self.user, name='Alimentação')

    def test_resolve_bank_exact_partial_match(self):
        self.assertEqual(resolve_bank(self.user, 'nubank'), self.bank)

    def test_resolve_bank_other_user_not_visible(self):
        self.assertIsNone(resolve_bank(self.other, 'nubank'))

    def test_resolve_bank_empty(self):
        self.assertIsNone(resolve_bank(self.user, ''))
        self.assertIsNone(resolve_bank(self.user, None))

    def test_resolve_category(self):
        self.assertEqual(resolve_category(self.user, 'alimentação'), self.category)

    def test_resolve_category_other_user_not_visible(self):
        self.assertIsNone(resolve_category(self.other, 'alimentação'))


class HandleOutflowTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.bank = make_bank(self.user)
        self.category = Category.objects.create(user=self.user, name='Alimentação')

    def test_register_outflow_success(self):
        response = handle_outflow(self.user, {
            'value': '45.90',
            'title': 'almoço',
            'bank': 'Nubank',
            'category': 'alimentação',
        })
        outflow = Outflow.objects.get()
        self.assertEqual(outflow.value, Decimal('45.90'))
        self.assertEqual(outflow.title, 'almoço')
        self.assertEqual(outflow.category, self.category)
        self.assertIn('Despesa registrada', response)

    def test_invalid_value(self):
        response = handle_outflow(self.user, {'value': None, 'bank': 'Nubank'})
        self.assertEqual(Outflow.objects.count(), 0)
        self.assertIn('Nao consegui identificar o valor', response)

    def test_unknown_bank(self):
        response = handle_outflow(self.user, {'value': '10.00', 'bank': 'Inexistente'})
        self.assertEqual(Outflow.objects.count(), 0)
        self.assertIn('Nao encontrei esse banco', response)

    def test_insufficient_balance(self):
        response = handle_outflow(self.user, {
            'value': '99999.00',
            'bank': 'Nubank',
            'category': None,
        })
        self.assertEqual(Outflow.objects.count(), 0)
        self.assertIn('Saldo insuficiente', response)


class HandleInflowTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.bank = make_bank(self.user)

    def test_register_inflow_success(self):
        response = handle_inflow(self.user, {'value': '500.00', 'bank': 'Nubank', 'title': 'freelance'})
        self.assertIn('Receita registrada', response)
        self.bank.refresh_from_db()
        self.assertEqual(self.bank.current_balance, Decimal('1500.00'))

    def test_unknown_bank(self):
        response = handle_inflow(self.user, {'value': '10.00', 'bank': 'Inexistente'})
        self.assertIn('Nao encontrei esse banco', response)


class HandleQueryTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.bank = make_bank(self.user)
        self.category = Category.objects.create(user=self.user, name='Alimentação')

    def test_bank_balance(self):
        response = handle_query(self.user, {
            'query_type': 'bank_balance',
            'bank': 'Nubank',
        })
        self.assertIn('R$ 1.000,00', response)

    def test_unknown_query_type(self):
        response = handle_query(self.user, {'query_type': 'unknown'})
        self.assertIn('Nao entendi', response)


class ProcessInterpretationTests(TestCase):

    def setUp(self):
        self.user = make_user()
        make_bank(self.user)

    @patch('integrations.handlers.interpret_message')
    def test_full_flow_outflow(self, mock_interpret):
        mock_interpret.return_value = {
            'intent': 'outflow',
            'value': '45.90',
            'title': 'almoço',
            'category': None,
            'bank': 'Nubank',
            'query_type': None,
        }
        from integrations.handlers import process_message
        response, interpretation = process_message(self.user, 'gastei 45,90 no almoço')
        self.assertEqual(Outflow.objects.count(), 1)
        self.assertIn('Despesa registrada', response)
        self.assertEqual(interpretation['intent'], 'outflow')

    @patch('integrations.handlers.interpret_message')
    def test_unknown_intent(self, mock_interpret):
        mock_interpret.return_value = {'intent': 'unknown'}
        from integrations.handlers import process_message
        response, _ = process_message(self.user, 'ola')
        self.assertIn('Nao entendi', response)


class ParseInterpretationTests(TestCase):

    def test_valid_json(self):
        from integrations.llm.base import parse_interpretation
        result = parse_interpretation(
            '{"intent": "outflow", "value": "45.90", "title": "almoço", '
            '"category": "alimentação", "bank": "Nubank", "query_type": null}'
        )
        self.assertEqual(result['intent'], 'outflow')
        self.assertEqual(result['value'], '45.90')

    def test_invalid_json_raises(self):
        from integrations.llm.base import LLMError, parse_interpretation
        with self.assertRaises(LLMError):
            parse_interpretation('nao sou json')

    def test_invalid_intent_normalized(self):
        from integrations.llm.base import parse_interpretation
        result = parse_interpretation('{"intent": "comprar"}')
        self.assertEqual(result['intent'], 'unknown')


class WebhookTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.binding = WhatsAppBinding.objects.create(
            user=self.user,
            phone='5511999999999',
        )
        self.url = reverse('integrations:whatsapp_webhook')
        self.headers = {'X-Webhook-Secret': 'troque-este-secret-webhook'}
        with patch('integrations.views.settings') as mock_settings:
            mock_settings.WHATSAPP_WEBHOOK_SECRET = 'troque-este-secret-webhook'
            pass

    def _payload(self, message_id='MSG001'):
        return {
            'event': 'MESSAGES_UPSERT',
            'data': {
                'key': {
                    'id': message_id,
                    'remoteJid': '5511999999999@s.whatsapp.net',
                    'fromMe': False,
                },
                'message': {'conversation': 'Gastei R$ 45,90 no almoço'},
            },
        }

    def test_invalid_secret_forbidden(self):
        response = self.client.post(self.url, data={}, content_type='application/json',
                                    headers={'X-Webhook-Secret': 'errado'})
        self.assertEqual(response.status_code, 403)

    def test_missing_secret_forbidden(self):
        response = self.client.post(self.url, data={}, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    @patch('integrations.tasks.process_whatsapp_message.delay')
    def test_valid_message_dispatches_task(self, mock_delay):
        with patch('django.conf.settings.WHATSAPP_WEBHOOK_SECRET', 'troque-este-secret-webhook'):
            response = self.client.post(
                self.url,
                data=self._payload(),
                content_type='application/json',
                headers=self.headers,
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(WhatsAppMessageLog.objects.filter(message_id='MSG001').exists())
        mock_delay.assert_called_once_with('MSG001')

    @patch('integrations.tasks.process_whatsapp_message.delay')
    def test_duplicate_message_ignored(self, mock_delay):
        with patch('django.conf.settings.WHATSAPP_WEBHOOK_SECRET', 'troque-este-secret-webhook'):
            self.client.post(self.url, data=self._payload(), content_type='application/json',
                             headers=self.headers)
            response = self.client.post(self.url, data=self._payload(), content_type='application/json',
                                        headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(WhatsAppMessageLog.objects.count(), 1)
        mock_delay.assert_called_once()

    @patch('integrations.tasks.process_whatsapp_message.delay')
    def test_unbound_number_ignored(self, mock_delay):
        payload = self._payload()
        payload['data']['key']['remoteJid'] = '5511888888888@s.whatsapp.net'
        with patch('django.conf.settings.WHATSAPP_WEBHOOK_SECRET', 'troque-este-secret-webhook'):
            response = self.client.post(self.url, data=payload, content_type='application/json',
                                        headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(WhatsAppMessageLog.objects.count(), 1)
        log = WhatsAppMessageLog.objects.get()
        self.assertEqual(log.result_status, WhatsAppMessageLog.STATUS_IGNORED)
        mock_delay.assert_not_called()

    def test_non_message_event_ignored(self):
        payload = {'event': 'CONNECTION_UPDATE', 'data': {}}
        with patch('django.conf.settings.WHATSAPP_WEBHOOK_SECRET', 'troque-este-secret-webhook'):
            response = self.client.post(self.url, data=payload, content_type='application/json',
                                        headers=self.headers)
        self.assertEqual(response.status_code, 200)

    @patch('integrations.tasks.process_whatsapp_message.delay')
    def test_lowercase_event_accepted(self, mock_delay):
        payload = self._payload()
        payload['event'] = 'messages.upsert'
        with patch('django.conf.settings.WHATSAPP_WEBHOOK_SECRET', 'troque-este-secret-webhook'):
            response = self.client.post(self.url, data=payload, content_type='application/json',
                                        headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(WhatsAppMessageLog.objects.filter(message_id='MSG001').exists())
        mock_delay.assert_called_once()

    @patch('integrations.tasks.process_whatsapp_message.delay')
    def test_bot_reply_echo_ignored(self, mock_delay):
        WhatsAppMessageLog.objects.create(
            binding=self.binding,
            message_id='MSG001',
            direction=WhatsAppMessageLog.DIRECTION_OUT,
            phone='5511999999999',
            message_text='Saldo atual do Itau: R$ 149,66.',
        )
        payload = self._payload()
        payload['data']['key']['fromMe'] = True
        with patch('django.conf.settings.WHATSAPP_WEBHOOK_SECRET', 'troque-este-secret-webhook'):
            response = self.client.post(self.url, data=payload, content_type='application/json',
                                        headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(WhatsAppMessageLog.objects.filter(message_id='MSG001').count(), 1)
        mock_delay.assert_not_called()


class TaskTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.bank = make_bank(self.user)
        self.binding = WhatsAppBinding.objects.create(user=self.user, phone='5511999999999')
        self.log = WhatsAppMessageLog.objects.create(
            binding=self.binding,
            message_id='MSG001',
            direction=WhatsAppMessageLog.DIRECTION_IN,
            phone='5511999999999',
            message_text='Gastei R$ 45,90 no almoço, categoria alimentação, banco Nubank.',
        )

    @patch('integrations.tasks.send_whatsapp_reply.delay')
    @patch('integrations.handlers.interpret_message')
    def test_process_message_end_to_end(self, mock_interpret, mock_send):
        mock_interpret.return_value = {
            'intent': 'outflow',
            'value': '45.90',
            'title': 'almoço',
            'category': 'alimentação',
            'bank': 'Nubank',
            'query_type': None,
        }
        from integrations.tasks import process_whatsapp_message
        process_whatsapp_message('MSG001')
        self.log.refresh_from_db()
        self.assertEqual(self.log.result_status, WhatsAppMessageLog.STATUS_PROCESSED)
        self.assertEqual(self.log.interpreted_intent, 'outflow')
        self.assertEqual(Outflow.objects.count(), 1)
        mock_send.assert_called_once()
