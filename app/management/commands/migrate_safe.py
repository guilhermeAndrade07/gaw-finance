from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = (
        'Run migrations with a PostgreSQL advisory lock to prevent '
        'concurrent migration execution across multiple replicas.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            default=False,
            help='Do not prompt for user input.',
        )

    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            call_command('migrate', interactive=not options['no_input'])
            return

        lock_key = 1

        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_lock(%s)', [lock_key])
            self.stdout.write('Acquired advisory lock for migrations.')
            try:
                call_command('migrate', interactive=not options['no_input'])
            finally:
                cursor.execute('SELECT pg_advisory_unlock(%s)', [lock_key])
                self.stdout.write('Released advisory lock.')
