from django.core.management.base import BaseCommand

from signatures.services import generate_signature_charges


class Command(BaseCommand):
    help = 'Gera cobrancas de assinaturas ativas no cartao de credito para o mes corrente.'

    def handle(self, *args, **options):
        generate_signature_charges()
        self.stdout.write(self.style.SUCCESS('Cobrancas de assinaturas geradas com sucesso.'))
