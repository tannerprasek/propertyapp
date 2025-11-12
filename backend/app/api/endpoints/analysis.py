"""Analysis and mispricing detection endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_session
from app.schemas import ScanResultsResponse, MispricedOpportunity, Recommendation

router = APIRouter()

@router.post("/scan")
async def scan_transcripts(
    days: int = 7,
    session: AsyncSession = Depends(get_session),
):
    """Scan transcripts for all markets in the past N days."""
    return {
        "status": "scanning",
        "days": days,
        "message": "Starting transcript scan"
    }

@router.get("/results")
async def get_scan_results(
    session: AsyncSession = Depends(get_session),
) -> ScanResultsResponse:
    """Get latest scan results."""
    return ScanResultsResponse(
        total_markets=0,
        markets_scanned=0,
        companies_analyzed=0,
        total_mentions_found=0,
        mispriced_opportunities=[],
        scan_timestamp=datetime.now()
    )

@router.get("/mispriced")
async def get_mispriced_opportunities(
    min_mispricing: float = 0.1,
    session: AsyncSession = Depends(get_session),
):
    """Get current mispriced opportunities ranked by potential."""
    return {
        "opportunities": [],
        "min_mispricing_threshold": min_mispricing,
        "timestamp": datetime.now()
    }

@router.get("/market/{market_id}/analysis")
async def analyze_market(
    market_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get detailed analysis for a specific market."""
    return {
        "market_id": market_id,
        "analysis": "Detailed market analysis",
        "mentions": [],
        "model_results": {}
    }

@router.post("/analyze-ticker/{ticker}")
async def analyze_ticker(
    ticker: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Comprehensive analysis of a stock ticker:
    1. Fetch Polymarket markets for this ticker
    2. Pull 2 years of earnings call transcripts
    3. Scan transcripts for keywords from the markets
    4. Use probability model to identify mispriced odds
    5. Return highlighted opportunities
    """
    import logging
    from app.integrations.polymarket import PolymarketAPI
    from app.integrations.transcript_providers import fetch_all_company_transcripts
    from app.processing.keyword_matcher import KeywordMatcher
    from app.analysis.probability_model import ProbabilityModel
    from datetime import datetime
    import re

    logger = logging.getLogger(__name__)
    ticker = ticker.upper()

    logger.info(f"Starting comprehensive analysis for {ticker}")

    # Step 1: Fetch Polymarket markets for this ticker
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
                    'keywords': keywords,
                    'current_yes_probability': yes_prob,
                    'current_no_probability': no_prob,
                    'volume': float(market.get('volume', 0)),
                    'liquidity': float(market.get('liquidity', 0)),
                })

    logger.info(f"Found {len(relevant_markets)} relevant markets for {ticker}")

    if not relevant_markets:
        return {
            'ticker': ticker,
            'markets_found': 0,
            'transcripts_analyzed': 0,
            'total_mentions': 0,
            'opportunities': [],
            'message': f'No Polymarket earnings markets found for {ticker}'
        }

    # Step 2: Fetch earnings call transcripts (2 years)
    logger.info(f"Fetching transcripts for {ticker}")
    transcripts = await fetch_all_company_transcripts(ticker, max_transcripts=8)

    logger.info(f"Fetched {len(transcripts)} transcripts for {ticker}")

    if not transcripts:
        return {
            'ticker': ticker,
            'markets_found': len(relevant_markets),
            'transcripts_analyzed': 0,
            'total_mentions': 0,
            'opportunities': [],
            'message': f'No earnings transcripts found for {ticker}'
        }

    # Step 3: Scan transcripts for keywords from markets
    matcher = KeywordMatcher()
    prob_model = ProbabilityModel()

    opportunities = []
    total_mentions = 0

    for market in relevant_markets:
        market_id = market['market_id']
        market_title = market['title']
        keywords = market['keywords']

        if not keywords:
            # Extract keywords from title
            words = re.findall(r'\b[a-zA-Z]{4,}\b', market_title.lower())
            keywords = [w for w in words if w not in ['will', 'says', 'mention', 'earnings', 'call']]

        # Search for these keywords in transcripts
        all_mentions = []
        for transcript in transcripts:
            content = transcript.get('content', '')
            if not content:
                continue

            # Find mentions of keywords
            mentions = matcher.find_keywords(content, keywords)

            for mention in mentions:
                # Analyze sentiment
                sentiment = matcher.analyze_sentiment(mention['context'])
                mention['sentiment'] = sentiment
                mention['transcript_date'] = transcript.get('date')
                mention['transcript_title'] = transcript.get('title')
                all_mentions.append(mention)

        if all_mentions:
            total_mentions += len(all_mentions)

            # Step 4: Calculate probability from historical data
            transcript_dates = [m['transcript_date'] for m in all_mentions]
            base_prob, analysis = prob_model.calculate_base_probability(
                all_mentions,
                transcript_dates
            )

            # Calculate mispricing
            market_prob = market['current_yes_probability']
            mispricing_data = prob_model.calculate_mispricing(
                base_prob,
                market_prob,
                analysis.get('average_confidence', 0.5)
            )

            # Only include if mispricing is significant (>5%)
            if mispricing_data['mispricing_percentage'] > 5.0:
                # Generate explanation
                explanation = (
                    f"Based on {len(all_mentions)} mentions across {len(transcripts)} transcripts "
                    f"from the past 2 years, the keyword appears {analysis['positive_ratio']:.0%} "
                    f"of the time in a positive context. "
                    f"The model calculates a {base_prob:.1%} probability, "
                    f"while the market is pricing it at {market_prob:.1%}. "
                    f"This represents a {mispricing_data['mispricing_percentage']:.1f}% mispricing."
                )

                opportunities.append({
                    'market_id': market_id,
                    'market_title': market_title,
                    'company': ticker,
                    'ticker': ticker,
                    'base_probability': base_prob,
                    'market_probability': market_prob,
                    'mispricing_percentage': mispricing_data['mispricing_percentage'],
                    'recommendation': mispricing_data['recommendation'],
                    'mention_count': len(all_mentions),
                    'confidence': analysis.get('average_confidence', 0.5),
                    'explanation': explanation,
                    'expected_value_yes': mispricing_data['expected_value_yes'],
                    'expected_value_no': mispricing_data['expected_value_no'],
                })

    # Sort opportunities by mispricing percentage (highest first)
    opportunities.sort(key=lambda x: x['mispricing_percentage'], reverse=True)

    logger.info(f"Analysis complete for {ticker}. Found {len(opportunities)} opportunities")

    return {
        'ticker': ticker,
        'markets_found': len(relevant_markets),
        'transcripts_analyzed': len(transcripts),
        'total_mentions': total_mentions,
        'opportunities': opportunities,
        'analysis_timestamp': datetime.now().isoformat()
    }
