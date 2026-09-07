"""
config.py
---------
Centraliza toda a configuração da aplicação. NADA de segredo é escrito
aqui — tudo vem de variáveis de ambiente, carregadas de um arquivo .env
que NÃO deve ser commitado no Git (veja .gitignore).
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Carrega o arquivo .env (se existir) para as variáveis de ambiente do processo
load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_base_url: str = os.getenv("PAPELIA_API_BASE_URL", "https://router.huggingface.co/v1")
    model: str = os.getenv("PAPELIA_MODEL", "meta-llama/Llama-3.1-8B-Instruct:novita")
    hf_token: str = os.getenv("HF_TOKEN", "")
    numero_perguntas: int = int(os.getenv("PAPELIA_NUM_PERGUNTAS", "3"))
    temperature: float = float(os.getenv("PAPELIA_TEMPERATURE", "0.3"))
    max_tokens: int = int(os.getenv("PAPELIA_MAX_TOKENS", "1024"))
    cors_allow_origins: str = os.getenv("PAPELIA_CORS_ORIGINS", "*")

    def validar(self) -> None:
        if not self.hf_token:
            raise ValueError(
                "HF_TOKEN ausente. Crie um arquivo .env na pasta backend/ "
                "com a linha: HF_TOKEN=seu_token_aqui"
            )


settings = Settings()
