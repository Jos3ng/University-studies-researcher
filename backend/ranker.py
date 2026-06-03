import os
import json


# ──────────────────────────────────────────────
# Modo LLM (Groq — gratuito)
# ──────────────────────────────────────────────

def _build_prompt(tema: str, papers: list) -> str:
    lista = []
    for i, p in enumerate(papers):
        abstract_preview = (p.get("abstract") or "")[:500]
        lista.append(
            f"[{i+1}] {p.get('title','')}\n"
            f"Ano: {p.get('year','?')} | Fonte: {p.get('source','?')} | Citações: {p.get('citation_count','?')}\n"
            f"Abstract: {abstract_preview}"
        )

    return f"""Você é um pesquisador especialista em IA e ciência de dados. O usuário quer artigos sobre: "{tema}"

Aqui estão {len(papers)} artigos encontrados:

{"".join(chr(10)+chr(10).join(lista))}

Para cada artigo, avalie e retorne APENAS JSON válido (sem markdown, sem explicação fora do JSON):
{{
  "resumo_area": "2 frases sobre o estado da arte nesse tema específico",
  "resultados": [
    {{
      "numero": 1,
      "relevancia": 9,
      "contribuicao": "Uma frase direta sobre o que esse artigo traz de novo",
      "tipo": "teórico | prático | survey | benchmark",
      "leia_primeiro": true
    }}
  ]
}}

Regras:
- relevancia: 0-10 (10 = essencial para o tema)
- leia_primeiro: true apenas para os 2 artigos mais importantes
- Ordene os resultados por relevância decrescente
- Se o abstract estiver vazio ou irrelevante, dê relevancia <= 3"""


def rank_with_groq(tema: str, papers: list) -> dict:
    from groq import Groq

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    prompt = _build_prompt(tema, papers)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


# ──────────────────────────────────────────────
# Modo Local (sentence-transformers — sem API)
# ──────────────────────────────────────────────

_model = None  # lazy load


def _get_local_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print("[Ranker] Carregando modelo local (primeira vez ~30s)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def rank_local(tema: str, papers: list) -> dict:
    from sentence_transformers import util

    model = _get_local_model()
    query_emb = model.encode(tema, convert_to_tensor=True)

    scored = []
    for i, p in enumerate(papers):
        texto = f"{p.get('title','')} {(p.get('abstract') or '')[:400]}"
        emb = model.encode(texto, convert_to_tensor=True)
        score = float(util.cos_sim(query_emb, emb))
        scored.append((i + 1, score, p))

    scored.sort(key=lambda x: x[1], reverse=True)

    resultados = []
    for rank, (num, score, p) in enumerate(scored):
        resultados.append({
            "numero": num,
            "relevancia": round(score * 10, 1),
            "contribuicao": "Ranking por similaridade semântica (modo offline)",
            "tipo": "desconhecido",
            "leia_primeiro": rank < 2,
        })

    return {
        "resumo_area": f"Resultados rankeados por similaridade semântica com o tema '{tema}'.",
        "resultados": resultados,
        "modo": "local",
    }


# ──────────────────────────────────────────────
# Função principal com fallback automático
# ──────────────────────────────────────────────

def rank_papers(tema: str, papers: list) -> dict:
    """
    Tenta ranquear com Groq (gratuito, requer GROQ_API_KEY no .env).
    Se não tiver chave ou falhar, usa modelo local como fallback.
    """
    groq_key = os.environ.get("GROQ_API_KEY")

    if groq_key:
        try:
            print("[Ranker] Usando Groq (LLM)...")
            result = rank_with_groq(tema, papers)
            result["modo"] = "llm"
            return result
        except Exception as e:
            print(f"[Ranker] Groq falhou ({e}), caindo para modo local...")

    print("[Ranker] Usando sentence-transformers (local)...")
    return rank_local(tema, papers)
