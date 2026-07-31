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
