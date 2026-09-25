from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from auditing import actions
from auditing.services import record_audit_event
from categories.models import Category

from .models import InvestmentAsset, InvestmentMovement


def register_investment_movement(*, user, asset, operation_type, value, movement_date, register_cash_flow, notes=''):
    if value is None or value <= Decimal('0.00'):
        raise ValidationError('O valor da movimentacao deve ser maior que zero.')
    if operation_type not in {InvestmentMovement.APPORTION, InvestmentMovement.REDEMPTION}:
        raise ValidationError('Tipo de movimentacao invalido.')

    with transaction.atomic():
        locked_asset = InvestmentAsset.objects.select_for_update(of=('self',)).select_related(
            'bank',
        ).get(pk=asset.pk)

        if locked_asset.user_id != user.id:
            raise ValidationError('O ativo informado nao pertence ao usuario autenticado.')

        if operation_type == InvestmentMovement.REDEMPTION and value > locked_asset.current_value:
            raise ValidationError('O resgate nao pode ser maior que o valor atual do ativo.')

        movement = InvestmentMovement.objects.create(
            user=user,
            asset=locked_asset,
            operation_type=operation_type,
            value=value,
            movement_date=movement_date,
            register_cash_flow=register_cash_flow,
            notes=notes,
        )

        if operation_type == InvestmentMovement.APPORTION:
            if register_cash_flow:
                category, _ = Category.objects.get_or_create(
                    user=user,
                    name='Investimento',
                    defaults={'description': 'Aportes e movimentacoes de investimento'},
                )
                from outflows.services import register_outflow

                register_outflow(
                    user=user,
                    bank=locked_asset.bank,
                    value=value,
                    title=f'Aporte em investimento: {locked_asset.name}',
                    category=category,
                )
            locked_asset.current_value += value

        else:
            if register_cash_flow:
                from inflows.services import register_inflow

                register_inflow(
                    user=user,
                    bank=locked_asset.bank,
                    value=value,
                    title=f'Resgate de investimento: {locked_asset.name}',
                )
            locked_asset.current_value -= value

        locked_asset.save(update_fields=['current_value', 'update_at'])
        record_audit_event(
            action=actions.INVESTMENT_MOVEMENT_CREATE,
            user=user,
            resource_type='InvestmentMovement',
            resource_id=movement.pk,
            description='Movimentacao de investimento registrada.',
            metadata={
                'asset_id': locked_asset.pk,
                'operation_type': operation_type,
                'value': str(value),
                'register_cash_flow': register_cash_flow,
            },
        )
        return movement
