from django.contrib.auth.models import User
from django.test import TestCase, Client


class ReportViewTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_custom_report_requires_auth(self):
        c = Client()
        resp = c.get('/reports/custom/')
        self.assertEqual(resp.status_code, 302)

    def test_custom_report_pdf_default_sections(self):
        resp = self.client.get('/reports/custom/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')

    def test_custom_report_pdf_selected_sections(self):
        resp = self.client.get('/reports/custom/?sections=summary&sections=inflows')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')

    def test_custom_report_pdf_all_sections(self):
        resp = self.client.get(
            '/reports/custom/'
            '?sections=summary&sections=inflows&sections=outflows'
            '&sections=by_category&sections=investments'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')

    def test_custom_report_pdf_with_credit_card_section(self):
        resp = self.client.get('/reports/custom/?sections=summary&sections=credit_card')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')

    def test_investments_report_requires_auth(self):
        c = Client()
        resp = c.get('/reports/investments/')
        self.assertEqual(resp.status_code, 302)

    def test_investments_report_pdf(self):
        from .models import GeneratedReport

        resp = self.client.get('/reports/investments/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertIn('relatorio_investimentos', resp['Content-Disposition'])
        self.assertTrue(
            GeneratedReport.objects.filter(user=User.objects.get(username='testuser'), report_type='investments').exists()
        )

    def test_investments_report_pdf_with_assets(self):
        from decimal import Decimal
        from banks.models import Bank
        from investments.models import InvestmentAsset

        user = User.objects.get(username='testuser')
        bank = Bank.objects.create(
            user=user,
            name='Banco Principal',
            account_type='Corrente',
            agency=1,
            account=1,
        )
        InvestmentAsset.objects.create(
            user=user,
            bank=bank,
            name='Tesouro Selic',
            asset_type='RENDA_FIXA',
            institution='B3',
            current_value=Decimal('10000.00'),
        )

        resp = self.client.get('/reports/investments/')
        self.assertEqual(resp.status_code, 200)
        pdf_content = resp.content
        self.assertTrue(len(pdf_content) > 0)
        # PDF minimo gera bytes de conteudo apos o cabecalho
        self.assertTrue(b'PDF' in pdf_content[:8])
