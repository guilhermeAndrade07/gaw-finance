import calendar
from datetime import date

from django.db import transaction

from .models import Invoice, Payment


def _add_months(base_date, months):
    month_index = base_date.month - 1 + months
    year = base_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _clamp_day(year, month, day):
    last_day = calendar.monthrange(year, month)[1]
    return min(day, last_day)


def get_or_create_invoice_for_payment(card, purchase_date):
    """
    Determina (e cria se necessario) a fatura do cartao que deve receber a
    compra realizada em `purchase_date`.

    Regras:
    - Se o cartao nao tiver closing_day configurado, retorna None (sem ciclo).
    - Compra antes do dia de fechamento -> fatura do proprio mes da compra.
    - Compra no/apos o dia de fechamento -> fatura do mes seguinte.

    Calculo do vencimento (due_date):
    - due_day > closing_day -> vencimento no MESMO mes do fechamento.
    - due_day <= closing_day -> vencimento no mes SEGUINTE ao fechamento.
    """
    if card.closing_day is None or card.due_day is None:
        return None

    year = purchase_date.year
    month = purchase_date.month

    effective_closing_day = _clamp_day(year, month, card.closing_day)

    if purchase_date.day < effective_closing_day:
        closing_date = date(year, month, effective_closing_day)
    else:
        next_month = _add_months(date(year, month, 1), 1)
        closing_date = date(
            next_month.year,
            next_month.month,
            _clamp_day(next_month.year, next_month.month, card.closing_day),
        )

    if card.due_day > card.closing_day:
        due_date = date(
            closing_date.year,
            closing_date.month,
            _clamp_day(closing_date.year, closing_date.month, card.due_day),
        )
    else:
        next_month_after_close = _add_months(date(closing_date.year, closing_date.month, 1), 1)
        due_date = date(
            next_month_after_close.year,
            next_month_after_close.month,
            _clamp_day(
                next_month_after_close.year,
                next_month_after_close.month,
                card.due_day,
            ),
        )

    invoice, _ = Invoice.objects.get_or_create(
        card=card,
        closing_date=closing_date,
        defaults={'due_date': due_date, 'user': card.user},
    )
    return invoice


def assign_invoice_to_payment(payment):
    """
    Atribui a fatura correta ao payment com base no cartao e na data da compra.
    Idempotente: so salva se a fatura atribuida mudar.
    """
    if payment.card_id is None or payment.date_payment is None:
        return

    card = payment.card
    if card.closing_day is None or card.due_day is None:
        return

    invoice = get_or_create_invoice_for_payment(card, payment.date_payment)
    if invoice is None:
        return

    if payment.invoice_id != invoice.id:
        payment.invoice = invoice
        payment.save(update_fields=['invoice'])


@transaction.atomic
def close_past_invoices():
    """
    Fecha todas as faturas abertas cuja data de fechamento ja passou.
    """
    today = date.today()
    Invoice.objects.filter(
        status=Invoice.OPEN,
        closing_date__lt=today,
    ).update(status=Invoice.CLOSED)


@transaction.atomic
def backfill_invoices():
    """
    Atribui faturas a pagamentos existentes que ainda nao possuem invoice,
    desde que o cartao tenha ciclo de fatura configurado (closing_day/due_day).

    Util para migrar dados pre-existentes apos a criacao do sistema de faturas.
    """
    payments = Payment.objects.filter(
        invoice__isnull=True,
        card__isnull=False,
        date_payment__isnull=False,
        card__closing_day__isnull=False,
        card__due_day__isnull=False,
    ).select_related('card')

    for payment in payments:
        assign_invoice_to_payment(payment)
