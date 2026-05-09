from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from categories.models import Category
from inflows.models import Inflow
from outflows.models import Outflow

from .models import InvestmentMovement


def register_investment_movement(*, user, asset, operation_type, value, movement_date, register_cash_flow, notes=''):
    if asset.user_id != user.id:
        raise ValidationError('O ativo informado nao pertence ao usuario autenticado.')

    if value is None or value <= Decimal('0.00'):
        raise ValidationError('O valor da movimentacao deve ser maior que zero.')

    with transaction.atomic():
        movement = InvestmentMovement.objects.create(
            user=user,
            asset=asset,
            operation_type=operation_type,
            value=value,
            movement_date=movement_date,
            register_cash_flow=register_cash_flow,
            notes=notes,
        )

        if operation_type == InvestmentMovement.APPORTION:
            asset.current_value += value
            if register_cash_flow:
                category, _ = Category.objects.get_or_create(
                    user=user,
                    name='Investimento',
                    defaults={'description': 'Aportes e movimentacoes de investimento'},
                )
                Outflow.objects.create(
                    user=user,
                    title=f'Aporte em investimento: {asset.name}',
                    bank=asset.bank,
                    category=category,
                    value=value,
                )
        elif operation_type == InvestmentMovement.REDEMPTION:
            if value > asset.current_value:
                raise ValidationError('O resgate nao pode ser maior que o valor atual do ativo.')

            asset.current_value -= value
            if register_cash_flow:
                Inflow.objects.create(
                    user=user,
                    title=f'Resgate de investimento: {asset.name}',
                    bank=asset.bank,
                    value=value,
                )
        else:
            raise ValidationError('Tipo de movimentacao invalido.')

        asset.save(update_fields=['current_value', 'update_at'])
        return movement
