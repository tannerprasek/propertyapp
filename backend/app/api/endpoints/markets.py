"""Polymarket markets endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_session
from app.models import PolymarketMarket
from app.schemas import PolymarketMarketResponse, PolymarketMarketCreate

router = APIRouter()

@router.get("/", response_model=List[PolymarketMarketResponse])
async def list_markets(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """List all available Polymarket markets."""
    stmt = select(PolymarketMarket).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

@router.get("/{market_id}", response_model=PolymarketMarketResponse)
async def get_market(
    market_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get specific market details."""
    stmt = select(PolymarketMarket).where(PolymarketMarket.market_id == market_id)
    result = await session.execute(stmt)
    market = result.scalar_one_or_none()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    return market

@router.post("/", response_model=PolymarketMarketResponse)
async def create_market(
    market: PolymarketMarketCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new market record."""
    db_market = PolymarketMarket(**market.model_dump())
    session.add(db_market)
    await session.commit()
    await session.refresh(db_market)
    return db_market

@router.get("/sync/polymarket")
async def sync_polymarket_markets():
    """Sync markets from Polymarket API."""
    return {
        "status": "syncing",
        "message": "Polymarket markets sync started"
    }
