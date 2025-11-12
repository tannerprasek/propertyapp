"""Main API router combining all endpoint groups."""

from fastapi import APIRouter
from app.api.endpoints import markets, transcripts, analysis, companies

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(markets.router, prefix="/api/markets", tags=["Markets"])
api_router.include_router(transcripts.router, prefix="/api/transcripts", tags=["Transcripts"])
api_router.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
api_router.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
