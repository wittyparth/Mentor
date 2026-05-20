import httpx

from app.core.config import settings


async def search(
    queries: list[str],
    num_results: int = 5,
    use_autoprompt: bool = True,
    max_characters: int = 800,
) -> list[dict]:
    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in queries:
            try:
                resp = await client.post(
                    "https://api.exa.ai/search",
                    headers={
                        "x-api-key": settings.EXA_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": query,
                        "type": "neural",
                        "numResults": num_results,
                        "useAutoprompt": use_autoprompt,
                        "contents": {"text": {"maxCharacters": max_characters}},
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                results.append({"query": query, "results": data.get("results", [])})
            except Exception:
                results.append({"query": query, "results": []})
    return results


def format_search_results(results: list[dict], max_snippets: int = 3, max_chars: int = 800) -> str:
    sections = []
    for item in results:
        query = item.get("query", "")
        hits = item.get("results", [])[:max_snippets]
        if not hits:
            continue
        section = f"Query: {query}\n"
        for hit in hits:
            title = hit.get("title", "Untitled")
            snippet = (hit.get("text", "") or "")[:max_chars]
            section += f"- {title}: {snippet}\n"
        sections.append(section)
    return "\n".join(sections)