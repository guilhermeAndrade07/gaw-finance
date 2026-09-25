from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.models import Invite


class Command(BaseCommand):
    help = 'Cria um convite de uso unico para o proprietario da aplicacao.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--days', type=int, default=7)
        parser.add_argument('--base-url', dest='base_url', default='https://gawfinance.gawsystems.com.br')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        days = options['days']
        base_url = options['base_url'].rstrip('/')

        if User.objects.filter(email__iexact=email).exists():
            raise CommandError('Ja existe um usuario com este email.')

        if days < 1 or days > 30:
            raise CommandError('O convite deve expirar entre 1 e 30 dias.')

        token = Invite.generate_token()
        invite = Invite.objects.create(
            email=email,
            token_hash=Invite.hash_token(token),
            is_superuser=True,
            expires_at=timezone.now() + timedelta(days=days),
        )

        self.stdout.write(self.style.SUCCESS('Convite criado com sucesso.'))
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Expira em: {invite.expires_at.isoformat()}')
        self.stdout.write(f'URL de ativacao: {base_url}/invite/{token}/')
