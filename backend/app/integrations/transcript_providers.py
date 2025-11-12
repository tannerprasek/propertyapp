"""Integration with transcript service providers (SeekingAlpha, etc.)."""

import aiohttp
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class EarningsTranscriptFetcher:
    """Fetch earnings transcripts from various sources."""

    def __init__(self):
        """Initialize transcript fetcher."""
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def fetch_seeking_alpha(self, ticker: str, max_transcripts: int = 8) -> List[Dict]:
        """
        Fetch earnings transcripts from SeekingAlpha using their public API.

        Args:
            ticker: Stock ticker symbol
            max_transcripts: Maximum number of transcripts to fetch (default: 8, covers 2 years)

        Returns:
            List of transcript dictionaries
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        transcripts = []

        try:
            # SeekingAlpha API endpoint for earnings transcripts
            # Note: This is a simplified version - actual implementation may need API key
            url = f"https://seekingalpha.com/api/v3/symbols/{ticker}/transcripts"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with self.session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    # Parse the response
                    items = data.get('data', [])[:max_transcripts]

                    for item in items:
                        attributes = item.get('attributes', {})

                        # Fetch full transcript content
                        transcript_id = item.get('id')
                        content = await self._fetch_seeking_alpha_content(ticker, transcript_id)

                        transcripts.append({
                            'id': transcript_id,
                            'title': attributes.get('title'),
                            'date': datetime.fromisoformat(attributes.get('publishedOn', '').replace('Z', '+00:00')),
                            'content': content,
                            'source': 'SeekingAlpha',
                            'url': f"https://seekingalpha.com/article/{transcript_id}"
                        })

                    logger.info(f"Fetched {len(transcripts)} transcripts from SeekingAlpha for {ticker}")
                else:
                    logger.warning(f"SeekingAlpha returned status {response.status} for {ticker}")

        except Exception as e:
            logger.error(f"Error fetching SeekingAlpha transcripts: {e}")

        return transcripts

    async def _fetch_seeking_alpha_content(self, ticker: str, transcript_id: str) -> str:
        """Fetch full transcript content from SeekingAlpha."""
        try:
            url = f"https://seekingalpha.com/article/{transcript_id}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Extract transcript content (SeekingAlpha specific selectors)
                    content_div = soup.find('div', {'data-test-id': 'content-container'})
                    if content_div:
                        return content_div.get_text(separator='\n', strip=True)

        except Exception as e:
            logger.debug(f"Could not fetch content for {transcript_id}: {e}")

        return ""

    async def fetch_motley_fool(self, ticker: str, max_transcripts: int = 8) -> List[Dict]:
        """
        Fetch transcripts from Motley Fool earnings transcripts.

        Args:
            ticker: Stock ticker symbol
            max_transcripts: Maximum transcripts to fetch

        Returns:
            List of transcript dictionaries
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        transcripts = []

        try:
            # Motley Fool transcript search URL
            url = f"https://www.fool.com/quote/{ticker.lower()}/earnings-call-transcripts/"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with self.session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Find transcript links
                    transcript_links = soup.find_all('a', href=re.compile(r'/earnings/call-transcript/'))

                    for link in transcript_links[:max_transcripts]:
                        transcript_url = link.get('href')
                        if not transcript_url.startswith('http'):
                            transcript_url = f"https://www.fool.com{transcript_url}"

                        # Extract title and date
                        title = link.get_text(strip=True)

                        # Fetch full content
                        content = await self._fetch_motley_fool_content(transcript_url)

                        # Parse date from title or URL
                        date_match = re.search(r'(\d{4})-q(\d)', transcript_url.lower())
                        if date_match:
                            year = int(date_match.group(1))
                            quarter = int(date_match.group(2))
                            # Estimate date based on quarter
                            month = (quarter - 1) * 3 + 2  # Middle of quarter
                            date = datetime(year, month, 15)
                        else:
                            date = datetime.now()

                        transcripts.append({
                            'id': transcript_url,
                            'title': title,
                            'date': date,
                            'content': content,
                            'source': 'Motley Fool',
                            'url': transcript_url
                        })

                    logger.info(f"Fetched {len(transcripts)} transcripts from Motley Fool for {ticker}")

        except Exception as e:
            logger.error(f"Error fetching Motley Fool transcripts: {e}")

        return transcripts

    async def _fetch_motley_fool_content(self, url: str) -> str:
        """Fetch full transcript content from Motley Fool."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Extract main content
                    article = soup.find('article') or soup.find('div', class_='article-content')
                    if article:
                        return article.get_text(separator='\n', strip=True)

        except Exception as e:
            logger.debug(f"Could not fetch Motley Fool content: {e}")

        return ""

    async def fetch_investor_relations(self, company_website: str) -> List[Dict]:
        """
        Fetch transcripts from company's investor relations page.

        Args:
            company_website: Company website URL

        Returns:
            List of transcript dictionaries.
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        transcripts = []

        try:
            # Construct likely IR page URLs
            ir_urls = [
                f"{company_website}/investor-relations/",
                f"{company_website}/ir/",
                f"{company_website}/earnings/",
            ]

            for ir_url in ir_urls:
                try:
                    async with self.session.get(
                        ir_url,
                        timeout=aiohttp.ClientTimeout(total=10),
                        headers={"User-Agent": "Mozilla/5.0"}
                    ) as response:
                        if response.status == 200:
                            # Parse page for transcript links
                            # Implementation would use BeautifulSoup
                            pass
                except Exception as e:
                    logger.debug(f"Could not fetch {ir_url}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching investor relations transcripts: {e}")

        return transcripts

async def fetch_all_company_transcripts(
    ticker: str,
    max_transcripts: int = 8,
    website: Optional[str] = None
) -> List[Dict]:
    """
    Fetch transcripts from all available sources for a company.

    Args:
        ticker: Company ticker symbol
        max_transcripts: Maximum transcripts to fetch (default 8 = ~2 years)
        website: Company website URL

    Returns:
        List of transcript dictionaries with 'title', 'date', 'content', 'source', 'url'
    """
    all_transcripts = []

    # Fetch from multiple providers
    async with EarningsTranscriptFetcher() as fetcher:
        # Try SeekingAlpha first (most comprehensive)
        try:
            logger.info(f"Fetching SeekingAlpha transcripts for {ticker}")
            seeking_alpha = await fetcher.fetch_seeking_alpha(ticker, max_transcripts)
            all_transcripts.extend(seeking_alpha)
        except Exception as e:
            logger.error(f"Error fetching SeekingAlpha: {e}")

        # If we need more, try Motley Fool
        if len(all_transcripts) < max_transcripts:
            try:
                logger.info(f"Fetching Motley Fool transcripts for {ticker}")
                motley = await fetcher.fetch_motley_fool(ticker, max_transcripts - len(all_transcripts))
                all_transcripts.extend(motley)
            except Exception as e:
                logger.error(f"Error fetching Motley Fool: {e}")

        # Try investor relations page if provided
        if website and len(all_transcripts) < max_transcripts:
            try:
                logger.info(f"Fetching IR transcripts for {ticker}")
                ir_transcripts = await fetcher.fetch_investor_relations(website)
                all_transcripts.extend(ir_transcripts[:max_transcripts - len(all_transcripts)])
            except Exception as e:
                logger.error(f"Error fetching IR transcripts: {e}")

    # Sort by date (most recent first) and limit
    all_transcripts.sort(key=lambda x: x.get('date', datetime.min), reverse=True)
    all_transcripts = all_transcripts[:max_transcripts]

    # Filter to last 2 years
    two_years_ago = datetime.now() - timedelta(days=730)
    all_transcripts = [t for t in all_transcripts if t.get('date', datetime.min) > two_years_ago]

    logger.info(f"Total transcripts fetched for {ticker}: {len(all_transcripts)}")

    return all_transcripts
