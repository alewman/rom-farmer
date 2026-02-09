"""MCP tools for Wikipedia game search and info."""

from typing import Any, Optional


async def tool_wiki_search(
    query: str,
    limit: int = 10,
    section_filter: Optional[str] = None,
) -> dict[str, Any]:
    """Semantic search over Wikipedia game articles."""
    try:
        from romfarmer.metadata.wiki_search import WikiSearch
        search = WikiSearch()
        results = search.search(query=query, limit=limit, section_filter=section_filter)
        return {
            "query": query,
            "count": len(results),
            "results": [
                {
                    "game": r["article_title"],
                    "section": r["section"],
                    "score": round(r["score"], 3),
                    "content": r["content"][:500] + "..." if len(r["content"]) > 500 else r["content"],
                    "url": r["article_url"],
                }
                for r in results
            ],
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_wiki_game_info(game_title: str) -> dict[str, Any]:
    """Get Wikipedia information about a specific game."""
    try:
        from romfarmer.metadata.wiki_search import WikiSearch
        search = WikiSearch()
        info = search.get_game_info(game_title)

        if not info:
            return {
                "game_title": game_title,
                "found": False,
                "message": f"No Wikipedia article found for '{game_title}'",
            }

        sections_preview = {}
        for name, content in info["sections"].items():
            if len(content) > 1000:
                sections_preview[name] = content[:1000] + f"... ({len(content)} chars total)"
            else:
                sections_preview[name] = content

        return {
            "game_title": game_title,
            "found": True,
            "article_title": info["title"],
            "url": info["url"],
            "section_names": list(info["sections"].keys()),
            "sections": sections_preview,
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_wiki_get_section(
    game_title: str,
    section_name: str,
) -> dict[str, Any]:
    """Get a specific section from a game's Wikipedia article."""
    try:
        from romfarmer.metadata.wiki_search import WikiSearch
        search = WikiSearch()
        content = search.get_section(game_title, section_name)

        if not content:
            return {"game_title": game_title, "section_name": section_name, "found": False}

        return {
            "game_title": game_title,
            "section_name": section_name,
            "found": True,
            "content": content,
            "length": len(content),
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_wiki_stats() -> dict[str, Any]:
    """Get statistics about the Wikipedia game database."""
    try:
        from romfarmer.metadata.wiki_search import WikiSearch
        search = WikiSearch()
        stats = search.stats()
        return {
            "total_chunks": stats["total_chunks"],
            "total_articles": stats["total_articles"],
            "unique_games": stats["unique_games"],
            "avg_tokens_per_chunk": stats["avg_tokens_per_chunk"],
            "total_tokens": stats["total_tokens"],
            "estimated_words": stats["total_tokens"] // 1.3,
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_wiki_find_game(
    query: str,
    limit: int = 10,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Fuzzy search for game titles by name."""
    try:
        from romfarmer.metadata.wiki_search import WikiSearch
        search = WikiSearch()
        results = search.find_games(query=query, limit=limit, threshold=threshold)
        return {
            "query": query,
            "count": len(results),
            "matches": results,
            "best_match": results[0] if results else None,
        }
    except Exception as e:
        return {"error": str(e)}
