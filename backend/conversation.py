"""
conversation.py
----------------
No código original, existia UMA única conversa global (`conversa_atual`).
Isso funciona para um teste solo no Colab, mas quebra assim que duas
pessoas usam o chat ao mesmo tempo: as mensagens de uma se misturam nas
da outra. Aqui cada conversa é identificada por um `session_id` (gerado
pelo frontend e guardado no navegador), e vive num dicionário em memória.

Para uma empresa real, o próximo passo natural é trocar esse dicionário
por Redis ou um banco de dados — mas a interface (SessionStore) já fica
pronta para essa troca sem mudar as rotas do FastAPI.
"""

from typing import Dict, List


class Conversa:
    def __init__(self, prompt_sistema: str):
        self._historico: List[Dict[str, str]] = [{"role": "system", "content": prompt_sistema}]

    def adicionar_usuario(self, conteudo: str) -> None:
        self._historico.append({"role": "user", "content": conteudo})

    def adicionar_assistente(self, conteudo: str) -> None:
        self._historico.append({"role": "assistant", "content": conteudo})

    @property
    def historico(self) -> List[Dict[str, str]]:
        return list(self._historico)


class SessionStore:
    """Guarda uma Conversa por session_id. Troque por Redis/DB quando for para produção."""

    def __init__(self, prompt_sistema_factory):
        # prompt_sistema_factory: função que retorna o system prompt atual
        # (permite reconfigurar o número de perguntas sem reiniciar o servidor)
        self._prompt_sistema_factory = prompt_sistema_factory
        self._sessoes: Dict[str, Conversa] = {}

    def obter(self, session_id: str) -> Conversa:
        if session_id not in self._sessoes:
            self._sessoes[session_id] = Conversa(self._prompt_sistema_factory())
        return self._sessoes[session_id]

    def resetar(self, session_id: str) -> None:
        self._sessoes[session_id] = Conversa(self._prompt_sistema_factory())

    def resetar_tudo(self) -> None:
        self._sessoes.clear()
