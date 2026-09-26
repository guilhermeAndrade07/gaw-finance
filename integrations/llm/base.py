import json

INTENTS = ('outflow', 'inflow', 'query', 'unknown')
QUERY_TYPES = ('month_expenses', 'category_expenses', 'bank_balance', 'recent_outflows', 'unknown')

SYSTEM_PROMPT = (
    'Voce e um interpretador de mensagens financeiras em portugues brasileiro. '
    'Analise a mensagem do usuario e retorne APENAS um JSON valido, sem texto extra, '
    'com este formato exato:\n'
    '{\n'
    '  "intent": "outflow" | "inflow" | "query" | "unknown",\n'
    '  "value": string decimal com ponto (ex: "45.90") ou null,\n'
    '  "title": descricao curta em minusculas ou null,\n'
    '  "category": nome da categoria ou null,\n'
    '  "bank": nome do banco ou null,\n'
    '  "query_type": "month_expenses" | "category_expenses" | "bank_balance" | '
    '"recent_outflows" | "unknown" (apenas se intent=query, senao null)\n'
    '}\n'
    'Regras:\n'
    '- "gastei", "paguei", "comprei" => intent=outflow.\n'
    '- "recebi", "ganhei", "entrei" => intent=inflow.\n'
    '- perguntas sobre gastos/saldos/historico => intent=query.\n'
    '- Valores: "R$ 45,90" => "45.90". Se o valor tiver apenas "45" entenda como "45.00".\n'
    '- "quanto gastei esse mes" => query_type=month_expenses.\n'
    '- "quanto gastei com alimentacao" => query_type=category_expenses e category preenchida.\n'
    '- "quanto tenho no nubank" => query_type=bank_balance e bank preenchido.\n'
    '- "ultimas despesas" => query_type=recent_outflows.\n'
    '- Nao invente valores, categorias ou bancos que nao estao na mensagem.'
)

EXAMPLES = [
    {
        'role': 'user',
        'content': 'Gastei R$ 45,90 no almoço, categoria alimentação, banco Nubank.',
    },
    {
        'role': 'assistant',
        'content': json.dumps({
            'intent': 'outflow',
            'value': '45.90',
            'title': 'almoço',
            'category': 'alimentação',
            'bank': 'Nubank',
            'query_type': None,
        }, ensure_ascii=False),
    },
]


class LLMError(Exception):
    pass


def get_llm_client():
    from django.conf import settings

    if settings.LLM_PROVIDER == 'openai':
        from integrations.llm.openai_client import OpenAIClient
        return OpenAIClient()
    from integrations.llm.opencode_client import OpenCodeClient
    return OpenCodeClient()


def parse_interpretation(raw_text):
    try:
        data = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        raise LLMError('Resposta do LLM nao e um JSON valido.')
    if not isinstance(data, dict):
        raise LLMError('Resposta do LLM invalida.')
    intent = data.get('intent')
    if intent not in INTENTS:
        intent = 'unknown'
    query_type = data.get('query_type')
    if query_type not in QUERY_TYPES:
        query_type = None
    return {
        'intent': intent,
        'value': data.get('value'),
        'title': data.get('title'),
        'category': data.get('category'),
        'bank': data.get('bank'),
        'query_type': query_type,
    }
