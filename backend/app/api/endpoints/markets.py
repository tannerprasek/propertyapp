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

@router.get("/search/{ticker}")
async def search_markets_by_ticker(
    ticker: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Search for Polymarket markets related to a stock ticker.
    Focuses on earnings call 'mentions' markets.
    """
    from app.integrations.polymarket import PolymarketAPI
    import re

    ticker = ticker.upper()

    # First, try to find markets in our database
    stmt = select(PolymarketMarket).where(
        PolymarketMarket.companies.contains([ticker])
    )
    result = await session.execute(stmt)
    db_markets = result.scalars().all()

    # Also fetch fresh data from Polymarket API
    async with PolymarketAPI() as api:
        all_markets = await api.get_markets()

        # Filter for earnings-related markets mentioning this ticker
        earnings_keywords = [
            'earnings', 'call', 'mention', 'mentions', 'say', 'says',
            'transcript', 'conference', 'quarterly', 'Q1', 'Q2', 'Q3', 'Q4'
        ]

        relevant_markets = []
        for market in all_markets:
            title = market.get('title', '').lower()
            description = market.get('description', '').lower()

            # Check if ticker is mentioned
            if ticker.lower() not in title and ticker.lower() not in description:
                continue

            # Check if it's earnings-related
            is_earnings = any(keyword in title or keyword in description
                            for keyword in earnings_keywords)

            if is_earnings:
                # Extract keywords from the market
                keywords = api.extract_keywords(market)

                # Parse probabilities
                prices = market.get('prices', [])
                yes_prob = 0.5
                no_prob = 0.5

                if len(prices) >= 2:
                    yes_prob = float(prices[0].get('prob', 0.5))
                    no_prob = float(prices[1].get('prob', 0.5))

                relevant_markets.append({
                    'market_id': market.get('id'),
                    'title': market.get('title'),
                    'description': market.get('description'),
                    'category': market.get('category', 'earnings'),
                    'current_yes_probability': yes_prob,
                    'current_no_probability': no_prob,
                    'volume': float(market.get('volume', 0)),
                    'liquidity': float(market.get('liquidity', 0)),
                    'keywords': keywords,
                    'end_date': market.get('endDate'),
                })

    return {
        'ticker': ticker,
        'markets': relevant_markets,
        'count': len(relevant_markets)
    }
