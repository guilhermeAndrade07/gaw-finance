import requests

from django.conf import settings

from integrations.llm.base import EXAMPLES, LLMError, SYSTEM_PROMPT


class OpenAIClient:

    def interpret(self, text):
        if not settings.LLM_API_KEY:
            raise LLMError('LLM_API_KEY nao configurada.')

        base_url = (settings.LLM_BASE_URL or 'https://api.openai.com/v1').rstrip('/')

        response = requests.post(
            f'{base_url}/chat/completions',
            headers={
                'Authorization': f'Bearer {settings.LLM_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': settings.LLM_MODEL,
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    *EXAMPLES,
                    {'role': 'user', 'content': text},
                ],
                'temperature': 0,
                'max_tokens': 300,
                'response_format': {'type': 'json_object'},
            },
            timeout=30,
        )
        if response.status_code != 200:
            raise LLMError(f'LLM respondeu com status {response.status_code}.')

        try:
            content = response.json()['choices'][0]['message']['content']
        except (KeyError, IndexError, ValueError):
            raise LLMError('Resposta do LLM em formato inesperado.')

        return content
