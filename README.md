# Paper Curator — GIIA

Curador inteligente de artigos acadêmicos. Busca em tempo real no Semantic Scholar e arXiv,
e usa IA pra ranquear e resumir os artigos mais relevantes pro seu tema.

**100% gratuito.** Sem custos de API.

---

## Como rodar

### 1. Clone o repositório

```bash
git clone https://github.com/Jos3ng/University-studies-researcher.git
cd University-studies-researcher
```

### 2. Instale as dependências Python

> Precisa ter o **Python 3.9+** instalado. Baixe em [python.org](https://python.org) se necessário.

```bash
pip install -r requirements.txt
```

> Na primeira execução o modelo local (~80MB) será baixado automaticamente. Pode demorar alguns minutos.

### 3. Configure as chaves de API

Crie o arquivo `.env` na raiz do projeto:

```bash
cp .env.example .env
```

Edite o `.env` e preencha as chaves:

```
GROQ_API_KEY=sua_chave_aqui
SEMANTIC_SCHOLAR_API_KEY=sua_chave_aqui
```

#### Como obter as chaves (ambas gratuitas)

**Groq** — necessária para os resumos gerados por IA:
1. Crie uma conta em [console.groq.com](https://console.groq.com)
2. Vá em **API Keys → Create API Key**
3. Cole a chave no `.env`

**Semantic Scholar** — necessária para evitar rate limit nas buscas:
1. Preencha o formulário em [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api#api-key-form)
2. Aguarde o email de aprovação (pode levar alguns dias)
3. Cole a chave no `.env` quando chegar

> **Sem as chaves o sistema ainda funciona** — usa ranking semântico local e busca sem autenticação. Porém pode atingir rate limit com uso intenso.

### 4. Suba o servidor

```bash
cd backend
uvicorn main:app --reload
```

Acesse: [http://localhost:8000](http://localhost:8000)

### 5. Verifique o status

Acesse [http://localhost:8000/health](http://localhost:8000/health) para confirmar quais serviços estão ativos:

```json
{
  "status": "ok",
  "groq_configurado": true,
  "modo_ativo": "llm (Groq)"
}
```

---

## Como usar na próxima vez

Já instalou tudo? Na próxima vez é só:

```bash
cd University-studies-researcher/backend
uvicorn main:app --reload
```

---

## Arquitetura

```
Usuário
  │  digita tema
  ▼
FastAPI (backend/main.py)
  ├── Semantic Scholar API  (gratuita, chave opcional mas recomendada)
  ├── arXiv API             (gratuita, sem chave)
  │
  └── Ranker (backend/ranker.py)
        ├── Groq / Llama 3  → resumos + ranking por relevância  [se GROQ_API_KEY]
        └── sentence-transformers local → ranking semântico     [fallback sempre]
```

## Estrutura de arquivos

```
University-studies-researcher/
├── backend/
│   ├── main.py       — FastAPI, endpoint /buscar
│   ├── fetchers.py   — integrações com Semantic Scholar e arXiv
│   └── ranker.py     — lógica de ranking (Groq + fallback local)
├── frontend/
│   └── index.html    — interface completa (sem build, HTML puro)
├── requirements.txt
└── .env.example
```

## Limites dos tiers gratuitos

| Serviço | Limite |
|---|---|
| Groq (Llama 3 70B) | 14.400 req/dia |
| Semantic Scholar | ~1 req/segundo com chave |
| arXiv | ~3 req/segundo |

Para um grupo universitário esses limites nunca vão ser atingidos.

## Próximos passos sugeridos

- [ ] Exportar resultados em BibTeX
- [ ] Filtro por tipo (survey, benchmark, teórico)
- [ ] "Artigos similares" a partir de um que você curtiu
- [ ] Upload de PDF → sugestão de referências faltando
- [ ] Histórico de buscas salvo no navegador
