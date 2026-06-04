import httpx
import xml.etree.ElementTree as ET


async def search_semantic_scholar(query: str, limit: int = 8, year_from: int = None) -> list:
    """
    Busca artigos na Semantic Scholar API (gratuita, sem chave).
    Retorna lista de dicts com title, abstract, year, authors, citationCount, url.
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "fields": "title,abstract,year,authors,citationCount,externalIds,openAccessPdf",
        "limit": limit,
    }
    if year_from:
        params["year"] = f"{year_from}-"

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json().get("data", [])

        papers = []
        for p in data:
            papers.append({
                "source": "Semantic Scholar",
                "title": p.get("title", ""),
                "abstract": p.get("abstract", "") or "",
                "year": p.get("year"),
                "authors": [a["name"] for a in p.get("authors", [])[:3]],
                "citation_count": p.get("citationCount", 0),
                "url": (
                    p.get("openAccessPdf", {}).get("url")
                    or f"https://www.semanticscholar.org/paper/{p.get('paperId', '')}"
                ),
            })
        return papers

    except Exception as e:
        print(f"[Semantic Scholar] Erro: {e}")
        return []


async def search_arxiv(query: str, limit: int = 5, year_from: int = None) -> list:
    """
    Busca artigos na API do arXiv (gratuita, sem chave).
    Retorna lista de dicts com title, abstract, year, authors, url.
    """
    url = "https://export.arxiv.org/api/query"
    search_query = f"all:{query}"
    if year_from:
        search_query += f" AND submittedDate:[{year_from}01010000 TO 99991231235900]"

    params = {
        "search_query": search_query,
        "max_results": limit,
        "sortBy": "relevance",
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(r.text)

        papers = []
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            published_el = entry.find("atom:published", ns)
            link_el = entry.find("atom:id", ns)
            authors = [
                a.find("atom:name", ns).text
                for a in entry.findall("atom:author", ns)[:3]
                if a.find("atom:name", ns) is not None
            ]

            year = published_el.text[:4] if published_el is not None else None
            papers.append({
                "source": "arXiv",
                "title": title_el.text.strip().replace("\n", " ") if title_el is not None else "",
                "abstract": summary_el.text.strip().replace("\n", " ") if summary_el is not None else "",
                "year": int(year) if year else None,
                "authors": authors,
                "citation_count": None,
                "url": link_el.text.strip() if link_el is not None else "",
            })
        return papers

    except Exception as e:
        print(f"[arXiv] Erro: {e}")
        return []


def deduplicate(papers: list) -> list:
    """Remove artigos duplicados pelo título (normalizado)."""
    seen = set()
    unique = []
    for p in papers:
        key = p["title"].lower().strip()[:80]
        if key not in seen and len(key) > 5:
            seen.add(key)
            unique.append(p)
    return unique
