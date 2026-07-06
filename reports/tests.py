from django.test import TestCase, Client


class ReportViewTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_cash_flow_report_requires_auth(self):
        c = Client()
        resp = c.get('/reports/cash-flow/')
        self.assertEqual(resp.status_code, 302)

    def test_cash_flow_report_pdf(self):
        resp = self.client.get('/reports/cash-flow/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')

    def test_expenses_by_category_report_pdf(self):
        resp = self.client.get('/reports/expenses-by-category/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')

    def test_investments_report_pdf(self):
        resp = self.client.get('/reports/investments/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
