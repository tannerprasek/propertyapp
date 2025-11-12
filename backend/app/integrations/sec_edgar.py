"""SEC EDGAR integration for fetching company transcripts."""

import aiohttp
import logging
from typing import List, Dict, Optional
from datetime import datetime
import feedparser

logger = logging.getLogger(__name__)

class SECEdgarAPI:
    """Client for SEC EDGAR API."""

    BASE_URL = "https://data.sec.gov"
    SUBMISSIONS_URL = "https://www.sec.gov/cgi-bin/browse-edgar"

    def __init__(self):
        """Initialize SEC EDGAR API client."""
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def get_company_filings(self, cik: str, filing_type: str = "8-K") -> List[Dict]:
        """
        Get company filings from SEC.

        Args:
            cik: Company CIK number
            filing_type: Type of filing (8-K for current reports, etc.)

        Returns:
            List of filing dictionaries.
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            # Normalize CIK (pad with zeros)
            cik = str(cik).lstrip("0").zfill(10)

            params = {
                "action": "getcompany",
                "CIK": cik,
                "type": filing_type,
                "dateb": "",
                "owner": "exclude",
                "count": 100,
                "search_text": ""
            }

            async with self.session.get(
                self.SUBMISSIONS_URL,
                params=params,
                headers={"User-Agent": "Mozilla/5.0"}
            ) as response:
                if response.status == 200:
                    text = await response.text()
                    filings = self._parse_filings(text)
                    return filings
                else:
                    logger.error(f"SEC EDGAR error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching SEC filings for CIK {cik}: {e}")
            return []

    def _parse_filings(self, html: str) -> List[Dict]:
        """Parse HTML response to extract filing information."""
        # This is a simplified version - real implementation would use proper HTML parsing
        filings = []

        # In production, use BeautifulSoup for robust parsing
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Find filing table rows
            table = soup.find("table", {"class": "tableFile"})
            if table:
                rows = table.find_all("tr")[1:]  # Skip header

                for row in rows[:100]:  # Limit to 100
                    cells = row.find_all("td")
                    if len(cells) >= 4:
                        filing = {
                            "filing_date": cells[3].text.strip(),
                            "filing_type": cells[0].text.strip(),
                            "url": cells[1].find("a")["href"] if cells[1].find("a") else None,
                        }
                        filings.append(filing)

        except ImportError:
            logger.warning("BeautifulSoup not installed, returning empty filings")

        return filings

    async def get_filing_text(self, filing_url: str) -> Optional[str]:
        """Fetch the full text of a filing."""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            # Construct full URL if relative
            if not filing_url.startswith("http"):
                filing_url = f"{self.BASE_URL}{filing_url}"

            async with self.session.get(
                filing_url,
                headers={"User-Agent": "Mozilla/5.0"}
            ) as response:
                if response.status == 200:
                    return await response.text()
                return None

        except Exception as e:
            logger.error(f"Error fetching filing {filing_url}: {e}")
            return None

async def fetch_company_transcripts(
    session,
    company_cik: str,
    company_id: int,
    max_transcripts: int = 12
) -> List[Dict]:
    """
    Fetch company transcripts from SEC EDGAR.

    Args:
        session: SQLAlchemy async session
        company_cik: Company CIK number
        company_id: Database company ID
        max_transcripts: Maximum number of transcripts to fetch

    Returns:
        List of transcript dictionaries ready for database insertion.
    """
    from app.models import Transcript, TranscriptType

    transcripts = []

    async with SECEdgarAPI() as api:
        # Get 8-K filings (current reports that often contain earnings calls)
        filings = await api.get_company_filings(company_cik, filing_type="8-K")

        for filing in filings[:max_transcripts]:
            try:
                filing_text = await api.get_filing_text(filing.get("url"))

                if filing_text:
                    # Check if this looks like a transcript (contains common keywords)
                    if any(keyword in filing_text.lower() for keyword in
                           ["earnings call", "conference", "transcript", "participant"]):

                        transcript = {
                            "company_id": company_id,
                            "transcript_type": "earnings",
                            "title": f"Earnings Call - {filing.get('filing_date')}",
                            "date": datetime.strptime(filing.get("filing_date"), "%Y-%m-%d"),
                            "raw_text": filing_text,
                            "source": "sec_edgar",
                            "source_url": filing.get("url"),
                        }
                        transcripts.append(transcript)

            except Exception as e:
                logger.error(f"Error processing filing: {e}")
                continue

    return transcripts
