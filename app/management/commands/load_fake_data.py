from datetime import date, timedelta, datetime
from decimal import Decimal
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Account
from banks.models import Bank
from categories.models import Category
from inflows.models import Inflow
from outflows.models import Outflow
from payment.models import CreditCard, Payment
from signatures.models import Signature
from investments.models import InvestmentAsset


BANK_NAMES = ['Banco do Brasil', 'Itau', 'Bradesco', 'Nubank', 'Inter', 'Santander']
CATEGORIES = [
    ('Moradia', 'Aluguel, condominio, IPTU'),
    ('Alimentacao', 'Supermercado, restaurantes'),
    ('Transporte', 'Combustivel, transporte publico'),
    ('Saude', 'Plano de saude, farmacia'),
    ('Educacao', 'Cursos, livros, mensalidades'),
    ('Lazer', 'Cinema, viagens, jogos'),
    ('Compras', 'Roupas, eletronicos'),
    ('Servicos', 'Internet, telefone, luz, agua'),
]
SALARIES = [3500, 4200, 5800, 6500, 7200, 8900, 9500, 12000]
EXPENSES = [
    ('Aluguel', 'Moradia', 1200, 1800),
    ('Supermercado', 'Alimentacao', 400, 800),
    ('Restaurante', 'Alimentacao', 80, 250),
    ('Combustivel', 'Transporte', 200, 450),
    ('Uber', 'Transporte', 30, 120),
    ('Plano de Saude', 'Saude', 300, 600),
    ('Farmacia', 'Saude', 40, 180),
    ('Curso Online', 'Educacao', 150, 400),
    ('Cinema', 'Lazer', 40, 100),
    ('Streaming', 'Lazer', 30, 60),
    ('Roupas', 'Compras', 100, 500),
    ('Conta de Luz', 'Servicos', 80, 250),
    ('Conta de Agua', 'Servicos', 40, 120),
    ('Internet', 'Servicos', 80, 150),
    ('Telefone', 'Servicos', 50, 120),
]
SIGNATURES = [
    ('Netflix', 'Streaming de filmes e series', 55, 'Lazer'),
    ('Spotify', 'Streaming de musica', 22, 'Lazer'),
    ('Amazon Prime', 'Streaming e frete gratis', 20, 'Lazer'),
    ('Microsoft 365', 'Pacote office', 35, 'Servicos'),
    ('ChatGPT Plus', 'Assistente de IA', 110, 'Servicos'),
]
INVESTMENTS = [
    ('Tesouro Selic 2029', 'FIXED_INCOME', 'Tesouro Nacional', 'DI', 15000),
    ('CDB Banco X 110% CDI', 'FIXED_INCOME', 'Banco X', 'DI', 8000),
    ('Itau ITSA4', 'VARIABLE_INCOME', 'B3', 'AT_MATURITY', 5200),
    ('PETR4', 'VARIABLE_INCOME', 'B3', 'AT_MATURITY', 3400),
    ('Bitcoin', 'CRYPTO', 'Binance', 'DAILY_LIQUIDITY', 12000),
    ('Fundo Imobiliario MXRF11', 'FUNDS', 'B3', 'DAILY_LIQUIDITY', 6800),
]


class Command(BaseCommand):
    help = 'Load fake data into the system for demonstration purposes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            default='demo',
            help='Username for the demo user (default: demo).',
        )
        parser.add_argument(
            '--password',
            default='demo12345',
            help='Password for the demo user (default: demo12345).',
        )
        parser.add_argument(
            '--email',
            default='demo@gawfinance.com',
            help='Email for the demo user.',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            default=False,
            help='Delete existing data for the user before loading.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        reset = options['reset']

        if reset:
            self._reset_user(username)
            self.stdout.write(f'Cleared existing data for "{username}".')

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f'Created user "{username}" (password: {password}).')
        else:
            self.stdout.write(f'Using existing user "{username}".')

        Account.objects.get_or_create(user=user, defaults={'name': username})

        banks = self._create_banks(user)
        categories = self._create_categories(user)
        self._create_inflows(user, banks)
        self._create_outflows(user, banks, categories)
        cards = self._create_credit_cards(user, banks)
        self._create_payments(user, cards, categories)
        self._create_signatures(user, banks, categories)
        self._create_investments(user, banks)

        self.stdout.write(self.style.SUCCESS('Fake data loaded successfully.'))

    def _reset_user(self, username):
        try:
            user = User.objects.get(username=username)
            user.delete()
        except User.DoesNotExist:
            pass

    def _create_banks(self, user):
        banks = []
        for i, name in enumerate(BANK_NAMES[:3]):
            initial = Decimal(random.randint(1000, 50000) * 100) / 100
            bank, created = Bank.objects.get_or_create(
                user=user,
                name=name,
                defaults={
                    'account_type': random.choice(['Conta Corrente', 'Poupanca', 'Conta Digital']),
                    'agency': random.randint(1000, 9999),
                    'account': random.randint(10000, 99999),
                    'initial_balance': initial,
                    'balance': initial,
                },
            )
            banks.append(bank)
        return banks

    def _create_categories(self, user):
        cats = {}
        for name, desc in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                user=user,
                name=name,
                defaults={'description': desc},
            )
            cats[name] = cat
        return cats

    def _create_inflows(self, user, banks):
        today = date.today()
        for months_ago in range(8, -1, -1):
            d = today - timedelta(days=months_ago * 30)
            salary = Decimal(random.choice(SALARIES))
            Inflow.objects.create(
                user=user,
                title=f'Salario {d.strftime("%m/%Y")}',
                bank=random.choice(banks),
                value=salary,
                created_at=timezone.make_aware(
                    datetime(d.year, d.month, 5, 9, 0, 0)
                ),
            )
            if random.random() > 0.6:
                extra = Decimal(random.randint(200, 1500))
                Inflow.objects.create(
                    user=user,
                    title='Freelance',
                    bank=random.choice(banks),
                    value=extra,
                    created_at=timezone.make_aware(
                        datetime(d.year, d.month, random.randint(10, 25), 14, 0, 0)
                    ),
                )

    def _create_outflows(self, user, banks, categories):
        today = date.today()
        for months_ago in range(8, -1, -1):
            d = today - timedelta(days=months_ago * 30)
            for title, cat_name, min_v, max_v in EXPENSES:
                value = Decimal(random.randint(min_v * 100, max_v * 100)) / 100
                Outflow.objects.create(
                    user=user,
                    title=title,
                    bank=random.choice(banks),
                    category=categories[cat_name],
                    value=value,
                    created_at=timezone.make_aware(
                        datetime(d.year, d.month, random.randint(1, 28), 10, 0, 0)
                    ),
                )

    def _create_credit_cards(self, user, banks):
        cards = []
        card_names = ['Cartao Black', 'Cartao Gold', 'Cartao Platinum']
        for i, name in enumerate(card_names[:2]):
            card, _ = CreditCard.objects.get_or_create(
                user=user,
                name=name,
                defaults={
                    'bank': banks[i % len(banks)],
                    'credit_limit': Decimal(random.choice([3000, 5000, 8000, 12000])),
                    'active': True,
                },
            )
            cards.append(card)
        return cards

    def _create_payments(self, user, cards, categories):
        today = date.today()
        for months_ago in range(3, -1, -1):
            d = today - timedelta(days=months_ago * 30)
            for i in range(random.randint(2, 5)):
                cat = random.choice(list(categories.values()))
                value = Decimal(random.randint(50, 600))
                Payment.objects.create(
                    user=user,
                    card=random.choice(cards),
                    name=f'Compra Cartao {i + 1}',
                    description='Compra de demonstracao',
                    category=cat,
                    date_payment=d.replace(day=random.randint(1, 28)),
                    value=value,
                    parcelas=random.choice([1, 1, 1, 2, 3, 6, 10, 12]),
                    paid=months_ago > 0,
                )

    def _create_signatures(self, user, banks, categories):
        for name, desc, value, cat_name in SIGNATURES:
            Signature.objects.get_or_create(
                user=user,
                name=name,
                defaults={
                    'description': desc,
                    'value': Decimal(value),
                    'billing_day': random.randint(1, 28),
                    'is_active': True,
                    'bank': random.choice(banks),
                    'category': categories.get(cat_name),
                },
            )

    def _create_investments(self, user, banks):
        for name, asset_type, institution, liquidity, value in INVESTMENTS:
            InvestmentAsset.objects.get_or_create(
                user=user,
                name=name,
                defaults={
                    'asset_type': asset_type,
                    'subtype': 'Demonstracao',
                    'institution': institution,
                    'bank': random.choice(banks),
                    'current_value': Decimal(value),
                    'is_active': True,
                    'liquidity_type': liquidity,
                },
            )
