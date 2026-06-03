from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os

from dotenv import load_dotenv
load_dotenv()

from fetchers import search_semantic_scholar, search_arxiv, deduplicate
from ranker import rank_papers

app = FastAPI(title="Paper Curator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class BuscarRequest(BaseModel):
    tema: str
    year_from: Optional[int] = None
    limit: Optional[int] = 10


@app.post("/buscar")
async def buscar(req: BuscarRequest):
    tema = req.tema.strip()
    if not tema:
        raise HTTPException(status_code=400, detail="Tema não pode ser vazio.")

    # Busca paralela nas duas APIs
    ss_papers = await search_semantic_scholar(tema, limit=req.limit, year_from=req.year_from)
    arxiv_papers = await search_arxiv(tema, limit=5, year_from=req.year_from)

    todos = deduplicate(ss_papers + arxiv_papers)

    if not todos:
        raise HTTPException(status_code=404, detail="Nenhum artigo encontrado para esse tema.")

    # Limita a 12 pra não explodir o contexto do LLM
    todos = todos[:12]

    ranking = rank_papers(tema, todos)

    # Mescla avaliação do LLM com dados originais dos artigos
    resultados_enriquecidos = []
    for r in ranking.get("resultados", []):
        idx = r["numero"] - 1
        if 0 <= idx < len(todos):
            paper = todos[idx]
            resultados_enriquecidos.append({
                **r,
                "titulo": paper.get("title", ""),
                "ano": paper.get("year"),
                "autores": paper.get("authors", []),
                "citacoes": paper.get("citation_count"),
                "url": paper.get("url", ""),
                "fonte": paper.get("source", ""),
                "abstract": (paper.get("abstract") or "")[:300] + "...",
            })

    # Ordena por relevância
    resultados_enriquecidos.sort(key=lambda x: x.get("relevancia", 0), reverse=True)

    return {
        "tema": tema,
        "total_encontrado": len(todos),
        "modo": ranking.get("modo", "llm"),
        "resumo_area": ranking.get("resumo_area", ""),
        "resultados": resultados_enriquecidos,
    }


@app.get("/health")
def health():
    groq_configurado = bool(os.environ.get("GROQ_API_KEY"))
    return {
        "status": "ok",
        "groq_configurado": groq_configurado,
        "modo_ativo": "llm (Groq)" if groq_configurado else "local (sentence-transformers)",
    }


# Serve o frontend estático
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
