import json

from django.core.management.base import BaseCommand

from banks.services import reconcile_bank_balances


class Command(BaseCommand):
    help = 'Sincroniza Bank.balance com o saldo calculado a partir do historico.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplica as divergencias encontradas.',
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Retorna resultado em formato JSON.',
        )

    def handle(self, *args, **options):
        from banks.models import Bank

        divergences = []
        for bank in Bank.objects.all():
            if bank.balance != bank.current_balance:
                divergences.append({
                    'id': bank.pk,
                    'stored': str(bank.balance),
                    'calculated': str(bank.current_balance),
                })

        if options['apply']:
            updated = reconcile_bank_balances()
            payload = {'updated': len(updated), 'items': updated}
        else:
            payload = {'divergences': len(divergences), 'items': divergences}

        if options['json']:
            self.stdout.write(json.dumps(payload, ensure_ascii=False))
            if divergences and not options['apply']:
                self.stderr.write(f'Divergencias encontradas: {len(divergences)}')
                raise SystemExit(1)
        else:
            self.stdout.write(f"Divergencias: {len(divergences)}")
            if options['apply']:
                self.stdout.write(f"Saldos atualizados: {len(updated)}")
