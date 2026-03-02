"""
Analysis router - the core endpoint GET /analyze/{sector}
"""
import logging
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import PlainTextResponse, Response

from app.models.schemas import AnalysisResponse
from app.endpoint.services.analysis_service import analysis_service
from app.utils.auth import get_current_user
from app.utils.storage import storage

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_SECTOR_PATTERN = re.compile(r"^[a-zA-Z0-9\s\-]{2,100}$")

# Known sectors for documentation
EXAMPLE_SECTORS = [
    "pharmaceuticals", "technology", "agriculture", "automobile",
    "textiles", "fintech", "renewable-energy", "steel",
    "chemicals", "it-services", "food-processing", "defence",
    "gems-and-jewellery", "electronics", "logistics"
]


@router.get(
    "/{sector}",
    response_model=AnalysisResponse,
    summary="Analyze trade opportunities for a sector",
    description="""
Analyzes trade opportunities for the specified Indian market sector.

**Workflow:**
1. Validates the sector name
2. Searches for current market news and data
3. Uses Gemini AI to generate a structured analysis
4. Returns a comprehensive markdown report

**Example sectors:** `pharmaceuticals`, `technology`, `agriculture`, `automobile`, `textiles`, `fintech`

**Rate limit:** 10 requests per hour per user

**Caching:** Reports are cached for 30 minutes to improve performance
    """,
    responses={
        200: {"description": "Successful analysis report"},
        400: {"description": "Invalid sector name"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "External service unavailable"}
    }
)
async def analyze_sector(
    sector: str,
    request: Request,
    format: str = Query(default="json", enum=["json", "markdown"], description="Response format"),
    current_user: str = Depends(get_current_user)
):
    """
    Analyze trade opportunities for a given Indian market sector.
    
    - **sector**: The sector to analyze (e.g., `pharmaceuticals`, `technology`)
    - **format**: Response format - `json` (default) or `markdown` (raw .md text)
    
    Returns a structured market analysis report with opportunities, challenges, and recommendations.
    """
    # Input validation
    sector_clean = sector.strip().lower().replace(" ", "-")

    if not VALID_SECTOR_PATTERN.match(sector):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sector name '{sector}'. Use only letters, numbers, spaces, or hyphens. "
                   f"Examples: {', '.join(EXAMPLE_SECTORS[:5])}"
        )

    if len(sector_clean) < 2 or len(sector_clean) > 100:
        raise HTTPException(
            status_code=400,
            detail="Sector name must be between 2 and 100 characters."
        )

    # Get session ID
    session_id = getattr(request.state, "session_id", "unknown")

    logger.info(f"Analysis requested | user={current_user} | sector={sector_clean} | session={session_id}")

    try:
        result = await analysis_service.analyze_sector(sector_clean, session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed for {sector_clean}: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Analysis service temporarily unavailable. Please try again in a few minutes."
        )

    # Update user stats
    storage.increment_user_requests(current_user)

    # Return as raw markdown if requested
    if format == "markdown":
        return PlainTextResponse(
            content=result["report"],
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{sector_clean}-trade-report.md"',
                "X-Cached": str(result.get("cached", False)),
                "X-Sources-Searched": str(result.get("sources_searched", 0))
            }
        )

    return AnalysisResponse(
        sector=result["sector"],
        report=result["report"],
        generated_at=result["generated_at"],
        session_id=result["session_id"],
        cached=result.get("cached", False),
        sources_searched=result.get("sources_searched", 0)
    )


@router.get(
    "/",
    summary="List available sectors",
    description="Returns a list of example sectors that can be analyzed."
)
async def list_sectors(current_user: str = Depends(get_current_user)):
    """Get a list of example sectors available for analysis."""
    return {
        "message": "Use GET /analyze/{sector} to analyze any sector",
        "example_sectors": EXAMPLE_SECTORS,
        "usage": "GET /analyze/pharmaceuticals",
        "tip": "Add ?format=markdown to get a downloadable .md file"
    }