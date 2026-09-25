import calendar
from datetime import date

from django.db import transaction
from django.utils import timezone

from outflows.models import Outflow  # noqa: F401  mantido para compatibilidade retroativa
from payment.models import Payment
from .models import Signature, SignatureCharge


def generate_signature_charges():
    """
    Percorre todas as assinaturas ATIVAS com cartao de credito vinculado e
    gera um Payment (compra no cartao) para o mes corrente caso o dia de
    cobranca ja tenha sido alcancado e ainda nao tenha sido gerado neste mes.

    A geracao e idempotente: cada assinatura gera no maximo uma cobranca por
    mes, controlada pelos campos last_generated_month / last_generated_year.

    O date_payment do Payment reflete o dia real da cobranca (billing_day
    clampado para o ultimo dia valido do mes), e nao o dia em que o service
    rodou, para garantir que a cobranca seja atribuida ao ciclo correto.
    """
    today = timezone.localdate()
    active_signature_ids = Signature.objects.filter(
        is_active=True,
        credit_card__isnull=False,
    ).values_list('pk', flat=True)

    for signature_id in active_signature_ids:
        with transaction.atomic():
            signature = Signature.objects.select_for_update(of=('self',)).select_related(
                'credit_card',
                'category',
                'user',
            ).get(pk=signature_id)

            if not signature.is_active or signature.credit_card_id is None:
                continue

            if signature.last_generated_year is None or signature.last_generated_month is None:
                needs_generation = True
            elif today.year > signature.last_generated_year:
                needs_generation = True
            elif today.year == signature.last_generated_year and today.month > signature.last_generated_month:
                needs_generation = True
            else:
                needs_generation = False

            if not needs_generation:
                continue

            if signature.billing_day < 1 or signature.billing_day > 31:
                continue

            last_day_of_month = calendar.monthrange(today.year, today.month)[1]
            effective_billing_day = min(signature.billing_day, last_day_of_month)

            if today.day < effective_billing_day:
                continue

            charge_date = date(today.year, today.month, effective_billing_day)

            if SignatureCharge.objects.filter(
                signature=signature,
                reference_year=today.year,
                reference_month=today.month,
            ).exists():
                continue

            if Payment.objects.filter(
                user=signature.user,
                card=signature.credit_card,
                name=f'Assinatura: {signature.name}',
                date_payment=charge_date,
            ).exists():
                continue

            payment = Payment.objects.create(
                user=signature.user,
                card=signature.credit_card,
                name=f'Assinatura: {signature.name}',
                description=signature.description,
                category=signature.category,
                date_payment=charge_date,
                value=signature.value,
                parcelas=1,
                paid=False,
            )
            SignatureCharge.objects.create(
                signature=signature,
                payment=payment,
                reference_month=today.month,
                reference_year=today.year,
            )

            signature.last_generated_month = today.month
            signature.last_generated_year = today.year
            signature.save(update_fields=['last_generated_month', 'last_generated_year'])


def generate_signature_outflows():
    """
    Mantido por compatibilidade retroativa. Redireciona para a nova funcao
    que gera cobrancas no cartao de credito (Payment) em vez de Outflow.
    """
    generate_signature_charges()
