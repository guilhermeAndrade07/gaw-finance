from django.core.management.base import BaseCommand
from django.utils import timezone

from auditing.models import AuditEvent


class Command(BaseCommand):
    help = 'Remove eventos de auditoria anteriores ao periodo de retencao.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=365)
        parser.add_argument('--batch-size', type=int, default=1000)

    def handle(self, *args, **options):
        days = options['days']
        batch_size = options['batch_size']

        if days < 1 or batch_size < 1:
            raise ValueError('Os valores de dias e batch-size devem ser maiores que zero.')

        cutoff = timezone.now() - timezone.timedelta(days=days)
        deleted_total = 0

        while True:
            ids = list(
                AuditEvent.objects.filter(
                    created_at__lt=cutoff,
                ).values_list('pk', flat=True)[:batch_size]
            )
            if not ids:
                break

            deleted, _ = AuditEvent.objects.filter(pk__in=ids).delete()
            deleted_total += deleted

        self.stdout.write(
            f'Removidos {deleted_total} eventos de auditoria anteriores a {cutoff.isoformat()}.'
        )
