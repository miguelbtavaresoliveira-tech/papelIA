"""
llm_client.py
-------------
Encapsula a comunicação com o provedor de LLM (via API compatível com
OpenAI, roteada pela Hugging Face). Isolar isso numa classe própria
facilita trocar de provedor no futuro (ex.: migrar de Hugging Face para
a API da própria Anthropic/OpenAI) sem tocar nas rotas do FastAPI.
"""

import logging
import time
from typing import Dict, List

from openai import APIError, OpenAI

from config import Settings

logger = logging.getLogger("papelia.ai_client")


class ErroModeloIA(Exception):
    """Erro genérico ao chamar o modelo de IA, após esgotar as tentativas."""


class PapelIAClient:
    def __init__(self, settings: Settings):
        settings.validar()
        self._settings = settings
        self._client = OpenAI(base_url=settings.api_base_url, api_key=settings.hf_token)

    def perguntar(
        self,
        historico: List[Dict[str, str]],
        tentativas: int = 3,
        espera_segundos: float = 2.0,
    ) -> str:
        ultimo_erro = None
        for tentativa in range(1, tentativas + 1):
            try:
                resposta = self._client.chat.completions.create(
                    model=self._settings.model,
                    messages=historico,
                    temperature=self._settings.temperature,
                    max_tokens=self._settings.max_tokens,
                )
                return resposta.choices[0].message.content
            except APIError as erro:
                ultimo_erro = erro
                logger.warning("Tentativa %s/%s falhou: %s", tentativa, tentativas, erro)
                if tentativa < tentativas:
                    time.sleep(espera_segundos * tentativa)
        raise ErroModeloIA(f"Falha ao consultar o modelo após {tentativas} tentativas: {ultimo_erro}")
