import time

from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Wait for the database to be available.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='Timeout in seconds (default: 60).',
        )

    def handle(self, *args, **options):
        timeout = options['timeout']
        start = time.time()
        db_conn = connections['default']

        while True:
            try:
                db_conn.ensure_connection()
                self.stdout.write(self.style.SUCCESS('Database is available.'))
                return
            except OperationalError:
                if time.time() - start > timeout:
                    self.stdout.write(self.style.ERROR('Database not available.'))
                    raise SystemExit(1)
                time.sleep(1)
