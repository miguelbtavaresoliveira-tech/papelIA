"""
main.py
-------
Ponto de entrada da API. Roda localmente com:
    uvicorn main:app --reload --port 8000

Diferenças em relação ao script original de Colab:
  - Sem ngrok e sem `google.colab.userdata` (isso só existe dentro do Colab).
  - Sem tokens escritos no código: tudo vem de backend/.env (veja .env.example).
  - Cada usuário tem sua própria conversa (session_id), em vez de uma
    conversa global compartilhada por todo mundo que acessa a API.
"""

import logging

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from conversation import SessionStore
from llm_client import ErroModeloIA, PapelIAClient
from prompts import montar_prompt_sistema

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="PapelIA API")

# Em produção, troque "*" por uma lista explícita, ex.: ["https://seu-dominio.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_allow_origins] if settings.cors_allow_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = PapelIAClient(settings)
sessions = SessionStore(prompt_sistema_factory=lambda: montar_prompt_sistema(settings.numero_perguntas))


class MensagemRequest(BaseModel):
    mensagem: str


@app.get("/health")
async def health():
    """Endpoint simples para o frontend (ou um load balancer) checar se a API está de pé."""
    return {"status": "ok"}


@app.post("/chat")
async def chat_endpoint(req: MensagemRequest, x_session_id: str = Header(default="default")):
    conversa = sessions.obter(x_session_id)
    conversa.adicionar_usuario(req.mensagem)

    try:
        resposta_ia = client.perguntar(conversa.historico)
        conversa.adicionar_assistente(resposta_ia)
        return {"resposta": resposta_ia}
    except ErroModeloIA as e:
        logging.exception("Erro ao consultar o modelo")
        return {"erro": str(e)}


@app.post("/reset")
async def reset_endpoint(x_session_id: str = Header(default="default")):
    """Limpa o histórico de UMA sessão específica e começa um novo diagnóstico."""
    sessions.resetar(x_session_id)
    return {"status": "Histórico limpo. Pronto para novo diagnóstico."}
