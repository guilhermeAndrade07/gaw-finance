from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone

from inflows.services import register_inflow
from integrations.llm.base import LLMError
from integrations.llm.base import get_llm_client, parse_interpretation
from integrations.resolvers import resolve_bank, resolve_category
from outflows.models import Outflow
from outflows.services import register_outflow


def _fmt(value):
    value = Decimal(value).quantize(Decimal('0.01'))
    integer, decimal = divmod(value, 1)
    integer_text = f'{int(integer):,}'.replace(',', '.')
    decimal_text = f'{decimal * 100:02.0f}'
    return f'{integer_text},{decimal_text}'


def _format_money(value):
    return f'R$ {_fmt(value)}'


def interpret_message(text):
    client = get_llm_client()
    raw = client.interpret(text)
    return parse_interpretation(raw)


def _normalize_value(raw_value):
    if raw_value in (None, ''):
        return None
    try:
        value = Decimal(str(raw_value).replace(',', '.'))
    except (InvalidOperation, ValueError):
        return None
    if value <= 0:
        return None
    return value


def handle_outflow(user, interpretation):
    value = _normalize_value(interpretation.get('value'))
    if value is None:
        return 'Nao consegui identificar o valor da despesa. Tente: "gastei R$ 45,90 no almoço".'
    bank = resolve_bank(user, interpretation.get('bank'))
    if bank is None:
        return 'Nao encontrei esse banco no seu cadastro. Verifique o nome do banco e tente novamente.'
    title = interpretation.get('title') or 'Despesa via WhatsApp'
    category = resolve_category(user, interpretation.get('category'))
    try:
        outflow = register_outflow(
            user=user,
            bank=bank,
            value=value,
            title=title[:100],
            category=category,
        )
    except ValidationError as error:
        return f'Nao foi possivel registrar: {"; ".join(error.messages)}'
    category_text = f'\nCategoria: {category.name}' if category else ''
    return (
        f'Despesa registrada!\n'
        f'Valor: {_format_money(outflow.value)}\n'
        f'Descricao: {outflow.title}{category_text}\n'
        f'Banco: {bank.name}'
    )


def handle_inflow(user, interpretation):
    value = _normalize_value(interpretation.get('value'))
    if value is None:
        return 'Nao consegui identificar o valor da receita. Tente: "recebi R$ 1.000,00".'
    bank = resolve_bank(user, interpretation.get('bank'))
    if bank is None:
        return 'Nao encontrei esse banco no seu cadastro. Verifique o nome do banco e tente novamente.'
    title = interpretation.get('title') or 'Receita via WhatsApp'
    try:
        inflow = register_inflow(user=user, bank=bank, value=value, title=title[:100])
    except ValidationError as error:
        return f'Nao foi possivel registrar: {"; ".join(error.messages)}'
    return (
        f'Receita registrada!\n'
        f'Valor: {_format_money(inflow.value)}\n'
        f'Descricao: {inflow.title}\n'
        f'Banco: {bank.name}'
    )


def _query_month_expenses(user):
    now = timezone.localtime()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total = Outflow.objects.filter(user=user, created_at__gte=start).aggregate(
        total=Sum('value'),
    )['total'] or Decimal('0')
    return f'Voce gastou {_format_money(total)} neste mes.'


def _query_category_expenses(user, category_name):
    category = resolve_category(user, category_name)
    if category is None:
        return 'Nao encontrei essa categoria no seu cadastro.'
    total = Outflow.objects.filter(user=user, category=category).aggregate(
        total=Sum('value'),
    )['total'] or Decimal('0')
    return f'Voce gastou {_format_money(total)} com "{category.name}".'


def _query_bank_balance(user, bank_name):
    bank = resolve_bank(user, bank_name)
    if bank is None:
        return 'Nao encontrei esse banco no seu cadastro.'
    return f'Saldo atual do {bank.name}: {_format_money(bank.current_balance)}.'


def _query_recent_outflows(user, limit=5):
    outflows = Outflow.objects.filter(user=user).select_related('bank', 'category')[:limit]
    if not outflows:
        return 'Voce nao tem despesas registradas.'
    lines = ['Suas ultimas despesas:']
    for outflow in outflows:
        date = timezone.localtime(outflow.created_at).strftime('%d/%m')
        category = f' ({outflow.category.name})' if outflow.category else ''
        lines.append(f'- {date} {_format_money(outflow.value)} {outflow.title or "Despesa"}{category}')
    return '\n'.join(lines)


def handle_query(user, interpretation):
    query_type = interpretation.get('query_type') or 'unknown'
    handlers = {
        'month_expenses': lambda: _query_month_expenses(user),
        'category_expenses': lambda: _query_category_expenses(user, interpretation.get('category')),
        'bank_balance': lambda: _query_bank_balance(user, interpretation.get('bank')),
        'recent_outflows': lambda: _query_recent_outflows(user),
    }
    handler = handlers.get(query_type)
    if handler is None:
        return (
            'Nao entendi sua pergunta. Voce pode tentar:\n'
            '- "Quanto gastei esse mes?"\n'
            '- "Quanto gastei com alimentacao?"\n'
            '- "Quanto tenho no Nubank?"\n'
            '- "Ultimas 5 despesas"'
        )
    return handler()


def process_interpretation(user, interpretation):
    intent = interpretation.get('intent')
    if intent == 'outflow':
        return handle_outflow(user, interpretation)
    if intent == 'inflow':
        return handle_inflow(user, interpretation)
    if intent == 'query':
        return handle_query(user, interpretation)
    return (
        'Nao entendi sua mensagem. Exemplos do que posso fazer:\n'
        '- "Gastei R$ 45,90 no almoço, categoria alimentacao, banco Nubank"\n'
        '- "Recebi R$ 500,00"\n'
        '- "Quanto gastei esse mes?"'
    )


def process_message(user, text):
    try:
        interpretation = interpret_message(text)
    except LLMError:
        return 'Tive um problema para interpretar sua mensagem. Tente novamente em instantes.', None
    return process_interpretation(user, interpretation), interpretation
