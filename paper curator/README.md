# Paper Curator — GIIA

Curador inteligente de artigos acadêmicos. Busca em tempo real no Semantic Scholar e arXiv,
e usa IA pra ranquear e resumir os artigos mais relevantes pro seu tema.

**100% gratuito.** Sem custos de API.

---

## Como rodar

### 1. Clone e entre na pasta

```bash
git clone <seu-repo>
cd paper-curator
```

### 2. Instale as dependências Python

```bash
pip install -r requirements.txt
```

> Na primeira execução, o modelo local (~80MB) será baixado automaticamente.

### 3. Configure a chave Groq (opcional, mas recomendado)

Crie uma conta gratuita em [console.groq.com](https://console.groq.com) e gere uma API key.
Depois copie o `.env.example`:

```bash
cp .env.example .env
# edite o .env e coloque sua chave
```

**Sem a chave**, o sistema ainda funciona — usa similaridade semântica local.
**Com a chave**, os artigos ganham resumos e avaliações geradas por IA (Llama 3 70B via Groq).

### 4. Suba o servidor

```bash
cd backend
uvicorn main:app --reload
```

Acesse: [http://localhost:8000](http://localhost:8000)

---

## Arquitetura

```
Usuário
  │  digita tema
  ▼
FastAPI (backend/main.py)
  ├── Semantic Scholar API  (gratuita, sem chave)
  ├── arXiv API             (gratuita, sem chave)
  │
  └── Ranker (backend/ranker.py)
        ├── Groq / Llama 3  → resumos + ranking por relevância  [se GROQ_API_KEY]
        └── sentence-transformers local → ranking semântico     [fallback sempre]
```

## Estrutura de arquivos

```
paper-curator/
├── backend/
│   ├── main.py       — FastAPI, endpoint /buscar
│   ├── fetchers.py   — integrações com Semantic Scholar e arXiv
│   └── ranker.py     — lógica de ranking (Groq + fallback local)
├── frontend/
│   └── index.html    — interface completa (sem build, HTML puro)
├── requirements.txt
└── .env.example
```

## Limites do tier gratuito do Groq

| Modelo | Req/minuto | Req/dia | Tokens/minuto |
|---|---|---|---|
| llama-3.3-70b-versatile | 30 | 14.400 | 6.000 |

Para um grupo universitário isso nunca vai acabar.

## Próximos passos sugeridos

- [ ] Exportar resultados em BibTeX
- [ ] Filtro por tipo (survey, benchmark, teórico)
- [ ] "Artigos similares" a partir de um que você curtiu
- [ ] Upload de PDF → sugestão de referências faltando
- [ ] Histórico de buscas salvo no navegador
