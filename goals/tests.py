from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from banks.models import Bank
from categories.models import Category
from goals.models import MonthlyGoal
from outflows.models import Outflow


class MonthlyGoalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user-goals', password='pass123')
        self.other_user = User.objects.create_user(username='user-other', password='pass123')
        self.category_food = Category.objects.create(user=self.user, name='Alimentacao')
        self.category_transport = Category.objects.create(user=self.user, name='Transporte')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Banco Goals',
            account_type='Corrente',
            agency=1,
            account=11,
            initial_balance=Decimal('5000.00'),
            balance=Decimal('5000.00'),
        )

    def _create_goal(self, category=None, value='300.00', month=8, year=2026):
        return MonthlyGoal.objects.create(
            user=self.user,
            category=category,
            value=Decimal(value),
            month=month,
            year=year,
        )

    def _create_outflow(self, value, category=None, day=10, month=8, year=2026):
        outflow = Outflow.objects.create(
            user=self.user,
            title='Gasto Teste',
            bank=self.bank,
            category=category,
            value=Decimal(value),
        )
        forced_date = datetime(year, month, day, 12, 0, 0)
        Outflow.objects.filter(pk=outflow.pk).update(created_at=forced_date)
        outflow.refresh_from_db()
        return outflow

    def test_goal_create_view_creates_goal(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('goal_create'),
            {
                'category': self.category_food.id,
                'value': '300.00',
                'month': '8',
                'year': '2026',
            },
        )
        self.assertRedirects(response, reverse('goal_list'))
        self.assertTrue(
            MonthlyGoal.objects.filter(
                user=self.user, category=self.category_food, month=8, year=2026,
            ).exists()
        )

    def test_goal_create_rejects_duplicate_for_same_user_category_month_year(self):
        self._create_goal(category=self.category_food, value='300.00', month=8, year=2026)
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('goal_create'),
            {
                'category': self.category_food.id,
                'value': '500.00',
                'month': '8',
                'year': '2026',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MonthlyGoal.objects.filter(user=self.user, month=8, year=2026).count(), 1)

    def test_goal_create_allows_same_category_different_month(self):
        self._create_goal(category=self.category_food, value='300.00', month=8, year=2026)
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('goal_create'),
            {
                'category': self.category_food.id,
                'value': '400.00',
                'month': '9',
                'year': '2026',
            },
        )
        self.assertRedirects(response, reverse('goal_list'))
        self.assertEqual(MonthlyGoal.objects.filter(user=self.user, category=self.category_food).count(), 2)

    def test_goal_create_rejects_zero_value(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('goal_create'),
            {
                'category': self.category_food.id,
                'value': '0.00',
                'month': '8',
                'year': '2026',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MonthlyGoal.objects.filter(user=self.user).exists())

    def test_goal_list_is_user_scoped(self):
        self._create_goal(category=self.category_food, value='300.00')
        MonthlyGoal.objects.create(
            user=self.other_user,
            category=self.category_food,
            value=Decimal('999.00'),
            month=8,
            year=2026,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('goal_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alimentacao')
        self.assertNotContains(response, '999')

    def test_goal_list_filters_by_month(self):
        self._create_goal(category=self.category_food, value='300.00', month=8, year=2026)
        self._create_goal(category=self.category_transport, value='200.00', month=9, year=2026)
        self.client.force_login(self.user)
        response = self.client.get(reverse('goal_list'), {'month': '8', 'year': '2026'})
        self.assertEqual(response.status_code, 200)
        goals = response.context['goals']
        self.assertEqual(len(goals), 1)
        self.assertEqual(goals[0].category, self.category_food)

    def test_goal_update_view(self):
        goal = self._create_goal(category=self.category_food, value='300.00')
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('goal_update', kwargs={'pk': goal.id}),
            {
                'category': self.category_food.id,
                'value': '500.00',
                'month': '8',
                'year': '2026',
            },
        )
        self.assertRedirects(response, reverse('goal_list'))
        goal.refresh_from_db()
        self.assertEqual(goal.value, Decimal('500.00'))

    def test_goal_delete_view(self):
        goal = self._create_goal(category=self.category_food, value='300.00')
        self.client.force_login(self.user)
        response = self.client.post(reverse('goal_delete', kwargs={'pk': goal.id}))
        self.assertRedirects(response, reverse('goal_list'))
        self.assertFalse(MonthlyGoal.objects.filter(pk=goal.id).exists())

    def test_goal_update_is_user_scoped(self):
        goal = self._create_goal(category=self.category_food, value='300.00')
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('goal_update', kwargs={'pk': goal.id}))
        self.assertEqual(response.status_code, 404)

    def test_goal_delete_is_user_scoped(self):
        goal = self._create_goal(category=self.category_food, value='300.00')
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('goal_delete', kwargs={'pk': goal.id}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(MonthlyGoal.objects.filter(pk=goal.id).exists())

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('goal_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_dashboard_shows_period_label_and_goals(self):
        self._create_goal(category=self.category_food, value='300.00', month=8, year=2026)
        self.client.force_login(self.user)
        response = self.client.get(reverse('goal_dashboard'), {'month': '8', 'year': '2026'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agosto de 2026')
        self.assertEqual(len(response.context['goals']), 1)

    def test_goal_progress_endpoint_returns_percentages(self):
        self._create_goal(category=self.category_food, value='300.00', month=8, year=2026)
        self._create_outflow(value='150.00', category=self.category_food)
        self.client.force_login(self.user)
        response = self.client.get(reverse('get_goal_progress'), {'month': '8', 'year': '2026'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('Alimentacao', data['labels'])
        idx = data['labels'].index('Alimentacao')
        self.assertAlmostEqual(data['percentages'][idx], 50.0)
        self.assertAlmostEqual(data['spent'][idx], 150.0)
        self.assertAlmostEqual(data['goals'][idx], 300.0)

    def test_goal_progress_endpoint_requires_month_year(self):
        self._create_goal(category=self.category_food, value='300.00')
        self.client.force_login(self.user)
        response = self.client.get(reverse('get_goal_progress'))
        self.assertEqual(response.status_code, 400)

    def test_get_goal_progress_metric_zero_when_no_outflows(self):
        from app import metrics
        self._create_goal(category=self.category_food, value='300.00', month=8, year=2026)
        progress = metrics.get_goal_progress(self.user, month=8, year=2026)
        import json
        labels = json.loads(progress['labels'])
        percentages = json.loads(progress['percentages'])
        self.assertEqual(labels, ['Alimentacao'])
        self.assertEqual(percentages, [0.0])

    def test_get_goal_progress_metric_supports_null_category(self):
        from app import metrics
        MonthlyGoal.objects.create(
            user=self.user, category=None, value=Decimal('200.00'),
            month=8, year=2026,
        )
        self._create_outflow(value='100.00', category=None)
        progress = metrics.get_goal_progress(self.user, month=8, year=2026)
        import json
        labels = json.loads(progress['labels'])
        percentages = json.loads(progress['percentages'])
        self.assertIn('Sem categoria', labels)
        idx = labels.index('Sem categoria')
        self.assertAlmostEqual(percentages[idx], 50.0)

    def test_get_goal_status_counts_classification(self):
        from app import metrics
        self._create_goal(category=self.category_food, value='100.00', month=8, year=2026)
        self._create_goal(category=self.category_transport, value='200.00', month=8, year=2026)
        MonthlyGoal.objects.create(
            user=self.user, category=None, value=Decimal('50.00'),
            month=8, year=2026,
        )
        self._create_outflow(value='40.00', category=self.category_food)
        self._create_outflow(value='250.00', category=self.category_transport)
        self._create_outflow(value='40.00', category=None)
        counts = metrics.get_goal_status_counts(self.user, month=8, year=2026)
        self.assertEqual(counts['ok'], 1)
        self.assertEqual(counts['warning'], 1)
        self.assertEqual(counts['exceeded'], 1)
        self.assertEqual(counts['total'], 3)

    def test_goal_default_initial_is_current_month_year(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('goal_create'))
        self.assertEqual(response.status_code, 200)
        today = date.today()
        self.assertEqual(response.context['form'].initial['month'], today.month)
        self.assertEqual(response.context['form'].initial['year'], today.year)

    def test_unique_constraint_rejects_duplicate_null_category(self):
        from django.db import IntegrityError, transaction
        self._create_goal(category=None, value='200.00', month=8, year=2026)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MonthlyGoal.objects.create(
                    user=self.user, category=None, value=Decimal('300.00'),
                    month=8, year=2026,
                )
