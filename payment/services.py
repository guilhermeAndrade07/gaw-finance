import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from auditing import actions
from auditing.services import record_audit_event
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


def _validate_payment_owner(user, card, category):
    if card.user_id != user.id:
        raise ValidationError('O cartao informado nao pertence ao usuario autenticado.')
    if category is not None and category.user_id != user.id:
        raise ValidationError('A categoria informada nao pertence ao usuario autenticado.')


def _validate_credit_limit(user, card, value):
    credit_used = Payment.objects.filter(
        user=user,
        card=card,
        paid=False,
    ).aggregate(total=Sum('value'))['total'] or Decimal('0.00')
    credit_available = max(card.credit_limit - credit_used, Decimal('0.00'))

    if value > credit_available:
        raise ValidationError(
            f'Limite insuficiente! Limite disponivel: R$ {credit_available}'
        )


def _installment_values(total_value, parcelas):
    if total_value is None or parcelas < 1:
        raise ValidationError('Os dados da compra sao invalidos.')

    installment_value = (Decimal(total_value) / Decimal(parcelas)).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP,
    )
    accumulated = Decimal('0.00')
    values = []

    for index in range(parcelas):
        if index == parcelas - 1:
            values.append((Decimal(total_value) - accumulated).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP,
            ))
        else:
            values.append(installment_value)
            accumulated += installment_value

    return values


@transaction.atomic
def register_payment(
    *,
    user,
    card,
    name,
    date_payment,
    value,
    parcelas=1,
    description=None,
    category=None,
    paid=False,
):
    _validate_payment_owner(user, card, category)

    if value is None or value <= Decimal('0.00'):
        raise ValidationError('O valor da compra deve ser maior que zero.')
    if parcelas < 1 or parcelas > 60:
        raise ValidationError('O numero de parcelas deve estar entre 1 e 60.')

    _validate_credit_limit(user, card, value)

    if parcelas == 1:
        payment = Payment.objects.create(
            user=user,
            card=card,
            name=name,
            description=description,
            category=category,
            date_payment=date_payment,
            value=value,
            parcelas=parcelas,
            paid=paid,
        )
        record_audit_event(
            action=actions.PAYMENT_CREATE,
            user=user,
            resource_type='Payment',
            resource_id=payment.pk,
            description='Compra registrada.',
            metadata={'value': str(value), 'parcelas': parcelas, 'card_id': card.pk},
        )
        return payment

    payments_to_create = []
    installment_values = _installment_values(value, parcelas)

    for index, current_value in enumerate(installment_values):
        current_date = _add_months(date_payment, index) if date_payment else None
        payments_to_create.append(
            Payment(
                user=user,
                card=card,
                name=f'{name} ({index + 1}/{parcelas})',
                description=description,
                category=category,
                date_payment=current_date,
                value=current_value,
                parcelas=parcelas,
                paid=paid,
            )
        )

    Payment.objects.bulk_create(payments_to_create)

    if card.closing_day is not None and card.due_day is not None:
        for payment in payments_to_create:
            if payment.pk:
                assign_invoice_to_payment(payment)

    record_audit_event(
        action=actions.PAYMENT_CREATE,
        user=user,
        resource_type='Payment',
        resource_id=payments_to_create[0].pk if payments_to_create else '',
        description='Compra parcelada registrada.',
        metadata={'value': str(value), 'parcelas': parcelas, 'card_id': card.pk},
    )
    return payments_to_create[0]


def _refresh_invoice_status(invoice):
    payments = invoice.payments.all()
    if not payments:
        return

    unpaid_count = payments.filter(paid=False).count()
    today = timezone.localdate()

    if unpaid_count == 0:
        invoice.status = Invoice.PAID
    elif invoice.status == Invoice.PAID:
        invoice.status = Invoice.CLOSED if invoice.closing_date < today else Invoice.OPEN
    else:
        return

    invoice.save(update_fields=['status', 'updated_at'])


@transaction.atomic
def mark_payment_paid(*, user, payment_id):
    invoice_id = Payment.objects.filter(pk=payment_id, user=user).values_list(
        'invoice_id', flat=True,
    ).first()
    if invoice_id is None and not Payment.objects.filter(pk=payment_id, user=user).exists():
        raise ValidationError('A compra nao pertence ao usuario autenticado.')

    with transaction.atomic():
        if invoice_id is not None:
            Invoice.objects.select_for_update().get(pk=invoice_id)

        payment = Payment.objects.select_for_update().get(pk=payment_id, user=user)
        changed = not payment.paid
        if not changed:
            return payment

        payment.paid = True
        payment.save(update_fields=['paid', 'update_at'])

        if payment.invoice_id:
            invoice = Invoice.objects.get(pk=payment.invoice_id)
            _refresh_invoice_status(invoice)

        payment._status_changed = changed
        if changed:
            record_audit_event(
                action=actions.PAYMENT_MARK_PAID,
                user=user,
                resource_type='Payment',
                resource_id=payment.pk,
                description='Compra marcada como paga.',
                metadata={'invoice_id': payment.invoice_id},
            )
        return payment


@transaction.atomic
def mark_payment_unpaid(*, user, payment_id):
    invoice_id = Payment.objects.filter(pk=payment_id, user=user).values_list(
        'invoice_id', flat=True,
    ).first()
    if invoice_id is None and not Payment.objects.filter(pk=payment_id, user=user).exists():
        raise ValidationError('A compra nao pertence ao usuario autenticado.')

    with transaction.atomic():
        if invoice_id is not None:
            Invoice.objects.select_for_update().get(pk=invoice_id)

        payment = Payment.objects.select_for_update().get(pk=payment_id, user=user)
        changed = payment.paid
        if not changed:
            return payment

        payment.paid = False
        payment.save(update_fields=['paid', 'update_at'])

        if payment.invoice_id:
            invoice = Invoice.objects.get(pk=payment.invoice_id)
            _refresh_invoice_status(invoice)

        payment._status_changed = changed
        if changed:
            record_audit_event(
                action=actions.PAYMENT_MARK_UNPAID,
                user=user,
                resource_type='Payment',
                resource_id=payment.pk,
                description='Compra desmarcada como paga.',
                metadata={'invoice_id': payment.invoice_id},
            )
        return payment


@transaction.atomic
def mark_invoice_paid(invoice):
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    changed = invoice.status != Invoice.PAID
    if not changed:
        invoice._status_changed = False
        return invoice

    invoice.status = Invoice.PAID
    invoice.save(update_fields=['status', 'updated_at'])
    invoice.payments.update(paid=True)
    invoice._status_changed = True
    record_audit_event(
        action=actions.INVOICE_MARK_PAID,
        user=invoice.user,
        resource_type='Invoice',
        resource_id=invoice.pk,
        description='Fatura marcada como paga.',
        metadata={'card_id': invoice.card_id},
    )
    return invoice


@transaction.atomic
def mark_invoice_unpaid(invoice):
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    changed = invoice.status == Invoice.PAID
    if not changed:
        invoice._status_changed = False
        return invoice

    today = timezone.localdate()
    invoice.status = Invoice.OPEN if invoice.closing_date >= today else Invoice.CLOSED
    invoice.save(update_fields=['status', 'updated_at'])
    invoice.payments.update(paid=False)
    invoice._status_changed = True
    record_audit_event(
        action=actions.INVOICE_MARK_UNPAID,
        user=invoice.user,
        resource_type='Invoice',
        resource_id=invoice.pk,
        description='Fatura desmarcada como paga.',
        metadata={'card_id': invoice.card_id},
    )
    return invoice


@transaction.atomic
def close_past_invoices():
    today = timezone.localdate()
    Invoice.objects.filter(
        status=Invoice.OPEN,
        closing_date__lt=today,
    ).update(status=Invoice.CLOSED)


@transaction.atomic
def backfill_invoices():
    payments = Payment.objects.filter(
        invoice__isnull=True,
        card__isnull=False,
        date_payment__isnull=False,
        card__closing_day__isnull=False,
        card__due_day__isnull=False,
    ).select_related('card')

    for payment in payments:
        assign_invoice_to_payment(payment)
