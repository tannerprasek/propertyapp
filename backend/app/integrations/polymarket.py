"""Polymarket API integration."""

import aiohttp
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from app.config import settings

logger = logging.getLogger(__name__)

class PolymarketAPI:
    """Client for Polymarket API."""

    BASE_URL = "https://clob.polymarket.com"
    GRAPH_URL = "https://api.polymarket.com/graphql"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Polymarket API client."""
        self.api_key = api_key or settings.POLYMARKET_API_KEY
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def get_markets(self) -> List[Dict]:
        """
        Fetch all available markets from Polymarket.

        Returns:
            List of market dictionaries with relevant fields.
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            # Query open markets
            query = """
            {
                markets(first: 100, orderBy: "volume", orderDirection: "desc") {
                    id
                    title
                    description
                    category
                    endDate
                    liquidity
                    volume
                    prices {
                        id
                        prob
                    }
                    tokens {
                        id
                        symbol
                    }
                }
            }
            """

            async with self.session.post(
                self.GRAPH_URL,
                json={"query": query},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    markets = data.get("data", {}).get("markets", [])
                    return markets
                else:
                    logger.error(f"Polymarket API error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching Polymarket markets: {e}")
            return []

    async def get_market_by_id(self, market_id: str) -> Optional[Dict]:
        """Get specific market details."""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            query = f"""
            {{
                market(id: "{market_id}") {{
                    id
                    title
                    description
                    category
                    endDate
                    liquidity
                    volume
                    prices {{
                        id
                        prob
                    }}
                }}
            }}
            """

            async with self.session.post(
                self.GRAPH_URL,
                json={"query": query},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {}).get("market")
                return None

        except Exception as e:
            logger.error(f"Error fetching market {market_id}: {e}")
            return None

    def extract_keywords(self, market_data: Dict) -> List[str]:
        """Extract searchable keywords from market title and description."""
        keywords = []

        # Add title words as keywords
        title = market_data.get("title", "").lower()
        description = market_data.get("description", "").lower()

        # Simple keyword extraction (can be improved with NLP)
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}

        for word in title.split():
            word = word.lower().strip(".,!?;:")
            if len(word) > 3 and word not in stop_words:
                keywords.append(word)

        return keywords

    def extract_companies(self, market_data: Dict) -> List[str]:
        """Extract company names/tickers from market data."""
        companies = []

        # This is a simplified version - would benefit from proper entity recognition
        title = market_data.get("title", "").upper()

        # Common ticker patterns
        import re
        ticker_pattern = r"\b[A-Z]{1,5}\b"
        tickers = re.findall(ticker_pattern, title)

        companies.extend(tickers)
        return list(set(companies))

async def sync_polymarket_markets(session):
    """
    Sync current Polymarket markets to database.

    Args:
        session: SQLAlchemy async session
    """
    from sqlalchemy.dialects.postgresql import insert
    from app.models import PolymarketMarket

    async with PolymarketAPI() as api:
        markets = await api.get_markets()

        for market_data in markets:
            market_id = market_data.get("id")

            # Parse probabilities
            prices = market_data.get("prices", [])
            yes_prob = 0.5
            no_prob = 0.5

            if len(prices) >= 2:
                yes_prob = float(prices[0].get("prob", 0.5))
                no_prob = float(prices[1].get("prob", 0.5))

            market = PolymarketMarket(
                market_id=market_id,
                title=market_data.get("title"),
                description=market_data.get("description"),
                category=market_data.get("category", "other"),
                end_date=datetime.fromisoformat(market_data.get("endDate", datetime.now().isoformat())),
                current_yes_probability=yes_prob,
                current_no_probability=no_prob,
                volume=float(market_data.get("volume", 0)),
                liquidity=float(market_data.get("liquidity", 0)),
                keywords=api.extract_keywords(market_data),
                companies=api.extract_companies(market_data),
            )

            # Upsert to handle duplicates
            stmt = insert(PolymarketMarket).values(**market.__dict__).on_conflict_do_update(
                index_elements=[PolymarketMarket.market_id],
                set_=dict(
                    title=market.title,
                    current_yes_probability=market.current_yes_probability,
                    current_no_probability=market.current_no_probability,
                    volume=market.volume,
                    liquidity=market.liquidity,
                    last_updated=datetime.now()
                )
            )

            await session.execute(stmt)

        await session.commit()
        logger.info(f"Synced {len(markets)} markets from Polymarket")
