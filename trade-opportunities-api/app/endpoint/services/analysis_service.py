"""
Analysis service - orchestrates search + AI analysis pipeline
"""
import logging
from datetime import datetime
from typing import Dict

from app.endpoint.services.search_service import WebSearchService
from app.endpoint.services.gemini_service import GeminiService
from app.utils.storage import storage
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AnalysisService:
    def __init__(self):
        self.search_service = WebSearchService()
        self.gemini_service = GeminiService()

    async def analyze_sector(self, sector: str, session_id: str) -> Dict:
        """
        Full pipeline:
        1. Check cache
        2. Search for market data
        3. AI analysis
        4. Cache & return
        """
        # 1. Check cache first
        cached = storage.get_cached_report(sector, settings.cache_ttl)
        if cached:
            logger.info(f"Cache hit for sector: {sector}")
            return {
                **cached,
                "cached": True,
                "session_id": session_id
            }

        logger.info(f"Starting fresh analysis for sector: {sector}")

        # 2. Collect market data
        try:
            search_data = await self.search_service.search_sector_data(sector)
            sources_count = len(search_data.get("results", []))
        except Exception as e:
            logger.error(f"Search failed for {sector}: {e}")
            search_data = {"results": [], "queries_used": [], "total_found": 0}
            sources_count = 0

        # 3. AI Analysis
        try:
            report = await self.gemini_service.generate_analysis(sector, search_data)
        except Exception as e:
            logger.error(f"AI analysis failed for {sector}: {e}")
            raise

        # 4. Build result
        result = {
            "sector": sector,
            "report": report,
            "generated_at": datetime.utcnow(),
            "session_id": session_id,
            "cached": False,
            "sources_searched": sources_count
        }

        # 5. Cache it
        storage.cache_report(sector, result, settings.cache_ttl)
        logger.info(f"Analysis complete for sector: {sector} ({sources_count} sources)")

        return result


# Singleton
analysis_service = AnalysisService()