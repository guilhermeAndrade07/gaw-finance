from django.core.management.base import BaseCommand

from payment.services import backfill_invoices


class Command(BaseCommand):
    help = 'Atribui faturas a pagamentos existentes sem invoice, com base no ciclo do cartao.'

    def handle(self, *args, **options):
        backfill_invoices()
        self.stdout.write(self.style.SUCCESS('Faturas atribuidas com sucesso.'))
