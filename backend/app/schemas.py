"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

# Enums
class TranscriptType(str, Enum):
    EARNINGS = "earnings"
    CONFERENCE = "conference"
    ANALYST_DAY = "analyst_day"
    SHAREHOLDER_MEETING = "shareholder_meeting"
    OTHER = "other"

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class Recommendation(str, Enum):
    BUY_YES = "buy_yes"
    BUY_NO = "buy_no"
    NEUTRAL = "neutral"

# Company Schemas
class CompanyBase(BaseModel):
    name: str
    ticker: str
    cik: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Polymarket Market Schemas
class PolymarketMarketBase(BaseModel):
    market_id: str
    title: str
    description: Optional[str] = None
    category: str
    end_date: datetime
    current_yes_probability: float = Field(ge=0, le=1)
    current_no_probability: float = Field(ge=0, le=1)
    volume: Optional[float] = None
    liquidity: Optional[float] = None
    keywords: List[str] = []
    companies: List[str] = []

class PolymarketMarketCreate(PolymarketMarketBase):
    pass

class PolymarketMarketResponse(PolymarketMarketBase):
    id: int
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Transcript Schemas
class TranscriptBase(BaseModel):
    transcript_type: TranscriptType
    title: str
    date: datetime
    raw_text: str
    source: str
    source_url: str

class TranscriptCreate(TranscriptBase):
    company_id: int

class TranscriptResponse(TranscriptBase):
    id: int
    company_id: int
    cleaned_text: Optional[str] = None
    processed: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TranscriptDetailResponse(TranscriptResponse):
    company: CompanyResponse
    mentions: List['MentionResponse'] = []

# Mention Schemas
class MentionBase(BaseModel):
    keyword: str
    context: str
    position_start: int
    position_end: int
    confidence_score: float = Field(ge=0, le=1)
    sentiment: Sentiment

class MentionCreate(MentionBase):
    transcript_id: int
    market_id: int

class MentionResponse(MentionBase):
    id: int
    transcript_id: int
    market_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Probability Model Schemas
class ProbabilityModelBase(BaseModel):
    market_id: str
    base_probability: float = Field(ge=0, le=1)
    market_probability: float = Field(ge=0, le=1)
    mention_count: int
    context_strength: float = Field(ge=0, le=1)
    positive_mentions: int
    negative_mentions: int
    neutral_mentions: int
    recommendation: Recommendation

class ProbabilityModelResponse(ProbabilityModelBase):
    id: int
    company_id: int
    model_version: str
    mispricing_ratio: float
    confidence_interval: float
    created_at: datetime
    calculated_at: datetime

    class Config:
        from_attributes = True

# Analysis Results Schemas
class MispricedOpportunity(BaseModel):
    market_id: str
    market_title: str
    company: str
    ticker: str
    base_probability: float
    market_probability: float
    mispricing_percentage: float
    recommendation: Recommendation
    mention_count: int
    confidence: float
    explanation: str

class ScanResultsResponse(BaseModel):
    total_markets: int
    markets_scanned: int
    companies_analyzed: int
    total_mentions_found: int
    mispriced_opportunities: List[MispricedOpportunity]
    scan_timestamp: datetime

# Update forward references
TranscriptDetailResponse.update_forward_refs()
