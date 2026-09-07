# PapelIA — MVP de assistente de diagnóstico de processo (papel/celulose)


## 1. O que o código original fazia (explicação)

O script era um notebook de Google Colab com 5 blocos:

1. **Configuração**: lia um token da Hugging Face (hardcoded ou do Colab) e
   montava um objeto `Settings` com o modelo LLM a usar (`Llama-3.1-8B-Instruct`
   via um roteador da Hugging Face), temperatura, etc.
2. **Prompts**: um texto gigante (`VARIAVEIS_DE_PROCESSO_EXEMPLO`) descrevendo,
   em detalhe técnico, as 9 etapas de uma máquina de papel (preparação de
   massa, caixa de entrada, mesa formadora, prensas, secarias, size press,
   calandra, enroladeira) e como cada uma afeta os testes de laboratório
   (tração, rasgo, Cobb, Gurley, etc.). Isso é injetado no *system prompt* do
   modelo — ou seja, é o "conhecimento de domínio" que faz o LLM responder
   como um engenheiro de papel, não como um chatbot genérico.
3. **Cliente da IA**: uma classe `PapelIAClient` que chama a API da Hugging
   Face (que é compatível com a API da OpenAI) e tem retry automático em
   caso de erro.
4. **API FastAPI**: duas rotas, `/chat` (recebe uma mensagem, adiciona ao
   histórico, manda pro modelo, devolve a resposta) e `/reset` (limpa o
   histórico). **Só existia UMA conversa global** — se duas pessoas usassem
   ao mesmo tempo, as conversas se misturariam.
5. **Exposição via ngrok**: como o Colab não tem um endereço de internet
   fixo, o script usava o ngrok para criar um túnel público temporário e
   rodava o servidor numa thread em segundo plano.

Em resumo: é um **backend de chat com um LLM especialista**, feito para
rodar dentro de um notebook. Fora do Colab, os pontos 1 e 5 não fazem
sentido — e foi isso que eu removi/troquei abaixo.

## 2. O que eu mudei

| Original (Colab) | Agora (VSCode/local) |
|---|---|
| Token no código | Token em `.env`, fora do Git |
| `google.colab.userdata` | removido (não existe fora do Colab) |
| ngrok + thread manual | `uvicorn` normal, você roda no terminal |
| 1 conversa global (`conversa_atual`) | 1 conversa por sessão (`X-Session-Id`), guardada num dicionário em memória |
| tudo em 1 arquivo | dividido em `config.py`, `prompts.py`, `llm_client.py`, `conversation.py`, `main.py` |
| sem frontend | `frontend/index.html` — chat funcional, sem necessidade de build |

## 3. Arquitetura MVP

```
                    ┌─────────────────────────┐
                    │   frontend/index.html    │
                    │  (HTML + CSS + JS puro)  │
                    │  - gera um session_id    │
                    │  - manda POST /chat      │
                    └────────────┬─────────────┘
                                 │ HTTP (fetch)
                                 ▼
                    ┌─────────────────────────┐
                    │      backend (FastAPI)    │
                    │                           │
                    │  main.py     → rotas HTTP │
                    │  config.py   → .env       │
                    │  conversation.py → sessão │
                    │  prompts.py  → domínio    │
                    │  llm_client.py → chamada  │
                    └────────────┬─────────────┘
                                 │ HTTPS (API compatível OpenAI)
                                 ▼
                    ┌─────────────────────────┐
                    │  Hugging Face Router      │
                    │  (Llama-3.1-8B-Instruct)  │
                    └───────────────────────────┘
```

Por que essa divisão em arquivos (e não tudo num só, como no Colab)?
Porque cada peça pode evoluir sozinha sem quebrar as outras — por exemplo:
- Trocar o modelo de LLM (ou até trocar Hugging Face pela API da Anthropic/OpenAI direto) → só toca em `llm_client.py` e `config.py`.
- Guardar as conversas em Redis/banco em vez de memória (necessário assim que colocar em produção com múltiplos usuários e reinícios do servidor) → só toca em `conversation.py`.
- Melhorar a base de conhecimento do processo de papel, ou puxá-la de um banco/RAG em vez de um texto fixo → só toca em `prompts.py`.

## 4. Como rodar no VSCode

### Pré-requisitos
- Python 3.10+ instalado
- VSCode com a extensão "Python" (opcional, mas ajuda)

### Passo a passo

```bash
# 1. Entre na pasta do backend
cd papelIA/backend

# 2. Crie e ative um ambiente virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 3. Instale as dependências
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. Copie o arquivo de exemplo e preencha seu token NOVO
cp .env.example .env
# abra o .env no VSCode e cole o token novo da Hugging Face

# 5. Rode o servidor
uvicorn main:app --reload --port 8000
```

#6. Outra forma de rodar o servidor
```
.\.venv\Scripts\python -m uvicorn main:app --reload --port 8000
```

Se tudo estiver certo, o terminal mostra algo como:
```
Uvicorn running on http://127.0.0.1:8000
```

### Rodando o frontend

Não precisa de nada instalado — é um HTML puro:
- No VSCode, clique com o botão direito em `frontend/index.html` → "Open with Live Server" (se tiver a extensão), **ou**
- Simplesmente abra o arquivo `index.html` duas vezes no seu navegador (File → Open).

O indicador no topo direito do chat mostra "api conectada" quando o
backend (`uvicorn`) está rodando. Se aparecer "api offline", confira se o
terminal do backend ainda está de pé.

### Testando a API sozinha (sem frontend)

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-Id: teste-1" \
  -d '{"mensagem": "O papel está saindo com Cobb60 muito alto no lado tela."}'
```

## 5. Limitações deste MVP (e o que fazer antes de ir para os 500 milhões de faturamento)

Este projeto é um MVP — bom para validar a ideia com um punhado de usuários,
mas antes de apostar a margem de lucro de uma empresa grande nele, vale
resolver:

1. **Persistência real**: hoje as conversas ficam em memória — se o
   servidor reiniciar, tudo se perde. Trocar `conversation.py` para usar
   Redis ou Postgres.
2. **Autenticação**: hoje qualquer pessoa com a URL da API pode conversar.
   Adicionar login/API key por usuário.
3. **Observabilidade**: logar quais diagnósticos foram dados, para poder
   auditar se o modelo está certo (isso é especialmente importante numa
   aplicação industrial, onde um diagnóstico errado pode custar caro).
4. **Validação do modelo**: um LLM genérico (Llama 3.1 8B) "sabe" o que está
   no prompt, mas não tem garantia de precisão numérica. Para decisões que
   afetam produção real, vale ter um humano especialista revisando as
   sugestões antes de aplicá-las na máquina, pelo menos no início.
5. **Deploy**: quando quiser tirar do "local no VSCode" e colocar num
   servidor real, o ngrok não é adequado para produção (é uma ferramenta de
   desenvolvimento). As opções comuns são: um servidor próprio (VPS) atrás de
   HTTPS, ou serviços como Render/Railway/AWS/GCP.


