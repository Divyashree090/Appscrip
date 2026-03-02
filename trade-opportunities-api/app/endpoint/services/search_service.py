"""
Web search service - fetches market news and data for sectors
Uses DuckDuckGo search (no API key required)
"""
import asyncio
import logging
from typing import List, Dict
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TradeOpportunitiesBot/1.0)"
}


class WebSearchService:
    def __init__(self):
        self.timeout = httpx.Timeout(15.0)

    async def search_sector_data(self, sector: str) -> Dict[str, List[str]]:
        """
        Searches multiple queries about the sector and returns collected snippets
        """
        queries = [
            f"{sector} sector India trade opportunities 2024 2025",
            f"India {sector} industry export import trends",
            f"{sector} market growth India government policy",
            f"India {sector} sector challenges investment opportunities",
        ]

        all_results = []
        async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout) as client:
            tasks = [self._ddg_search(client, q) for q in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Search query {i} failed: {result}")
            elif result:
                all_results.extend(result)

        # Deduplicate
        seen = set()
        unique_results = []
        for r in all_results:
            key = r.get("title", "")
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        logger.info(f"Collected {len(unique_results)} search results for sector: {sector}")
        return {
            "results": unique_results[:20],  # Top 20 unique results
            "queries_used": queries,
            "total_found": len(unique_results)
        }

    async def _ddg_search(self, client: httpx.AsyncClient, query: str) -> List[Dict]:
        """Search DuckDuckGo HTML and parse results"""
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            response = await client.get(url)
            response.raise_for_status()
            return self._parse_ddg_html(response.text)
        except Exception as e:
            logger.error(f"DuckDuckGo search failed for '{query}': {e}")
            return []

    def _parse_ddg_html(self, html: str) -> List[Dict]:
        """Simple HTML parsing without BeautifulSoup for DuckDuckGo results"""
        import re
        results = []

        # Extract result blocks
        # DuckDuckGo result snippets pattern
        title_pattern = re.compile(r'class="result__title"[^>]*>.*?<a[^>]*>(.*?)</a>', re.DOTALL)
        snippet_pattern = re.compile(r'class="result__snippet"[^>]*>(.*?)</div>', re.DOTALL)
        url_pattern = re.compile(r'class="result__url"[^>]*>(.*?)</a>', re.DOTALL)

        titles = title_pattern.findall(html)
        snippets = snippet_pattern.findall(html)
        urls = url_pattern.findall(html)

        # Clean HTML tags
        def clean(text):
            text = re.sub(r'<[^>]+>', '', text)
            text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            text = text.replace('&#x27;', "'").replace('&quot;', '"').replace('&nbsp;', ' ')
            return ' '.join(text.split()).strip()

        for i in range(min(len(titles), len(snippets), 5)):
            title = clean(titles[i]) if i < len(titles) else ""
            snippet = clean(snippets[i]) if i < len(snippets) else ""
            url = clean(urls[i]) if i < len(urls) else ""

            if title or snippet:
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "url": url
                })

        return results