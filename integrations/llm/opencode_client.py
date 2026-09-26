import logging
import uuid

import requests

from django.conf import settings

from integrations.llm.base import EXAMPLES, LLMError, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class OpenCodeClient:

    def interpret(self, text):
        if not settings.LLM_API_KEY or not settings.LLM_BASE_URL:
            raise LLMError('LLM_API_KEY ou LLM_BASE_URL nao configurados.')

        session_id = str(uuid.uuid4())
        response = requests.post(
            f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions",
            headers={
                'Authorization': f'Bearer {settings.LLM_API_KEY}',
                'x-opencode-session': session_id,
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
