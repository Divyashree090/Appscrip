"""
Trade Opportunities API - Main Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import analyze, auth
from app.endpoint.middleware.rate_limiter import RateLimitMiddleware
from app.endpoint.middleware.session import SessionMiddleware
from app.utils.storage import storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Trade Opportunities API starting up...")
    yield
    logger.info("🛑 Trade Opportunities API shutting down...")
    storage.clear()


app = FastAPI(
    title="Trade Opportunities API",
    description="""
## Trade Opportunities API for Indian Market Sectors

Analyze trade opportunities across various Indian market sectors using AI-powered insights.

### Features
- 🔍 Real-time market analysis via AI
- 🔒 JWT Authentication
- ⚡ Rate limiting (10 requests/hour per user)
- 📊 Structured markdown reports
- 🛡️ Input validation & security

### Getting Started
1. Register: `POST /auth/register`
2. Login: `POST /auth/login` → get JWT token
3. Analyze: `GET /analyze/{sector}` with `Authorization: Bearer <token>`

### Supported Sectors (examples)
`pharmaceuticals`, `technology`, `agriculture`, `automobile`, `textiles`,
`fintech`, `renewable-energy`, `steel`, `chemicals`, `it-services`
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SessionMiddleware)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(analyze.router, prefix="/analyze", tags=["Market Analysis"])


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Trade Opportunities API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check"""
    stats = storage.get_stats()
    return {
        "status": "healthy",
        "active_sessions": stats["sessions"],
        "cached_reports": stats["reports"],
        "registered_users": stats["users"]
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )