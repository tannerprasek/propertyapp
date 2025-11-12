"""SQLAlchemy database models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base

class PolymarketMarket(Base):
    """Polymarket market/bet information."""
    __tablename__ = "polymarket_markets"

    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(String(255), unique=True, index=True)
    title = Column(String(500))
    description = Column(Text, nullable=True)
    category = Column(String(100))
    end_date = Column(DateTime)
    current_yes_probability = Column(Float)
    current_no_probability = Column(Float)
    volume = Column(Float)
    liquidity = Column(Float)
    keywords = Column(JSON)  # List of searchable keywords
    companies = Column(JSON)  # List of related companies
    last_updated = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    transcripts = relationship("Mention", back_populates="market")

class Company(Base):
    """Company information."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    ticker = Column(String(10), unique=True, index=True)
    cik = Column(String(20))  # SEC CIK number
    sector = Column(String(100))
    industry = Column(String(100))
    website = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    transcripts = relationship("Transcript", back_populates="company")

class Transcript(Base):
    """Company transcript data."""
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    transcript_type = Column(String(50))  # "earnings", "conference", "analyst_day", etc.
    title = Column(String(500))
    date = Column(DateTime, index=True)
    raw_text = Column(Text)
    cleaned_text = Column(Text, nullable=True)
    processed = Column(Boolean, default=False)
    source = Column(String(100))  # "sec_edgar", "seekingalpha", etc.
    source_url = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="transcripts")
    mentions = relationship("Mention", back_populates="transcript")

class Mention(Base):
    """Mentions of Polymarket keywords in transcripts."""
    __tablename__ = "mentions"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"))
    market_id = Column(Integer, ForeignKey("polymarket_markets.id"))
    keyword = Column(String(255), index=True)
    context = Column(Text)  # Surrounding text for context
    position_start = Column(Integer)  # Character position in text
    position_end = Column(Integer)
    confidence_score = Column(Float)  # 0-1, how confident this is a relevant mention
    sentiment = Column(String(20))  # "positive", "negative", "neutral"
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    transcript = relationship("Transcript", back_populates="mentions")
    market = relationship("PolymarketMarket", back_populates="transcripts")

class ProbabilityModel(Base):
    """Probability model results for mispricing detection."""
    __tablename__ = "probability_models"

    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(String(255), index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    model_version = Column(String(50))  # e.g., "v1.0"

    # Probabilities
    base_probability = Column(Float)  # Base probability from transcripts
    market_probability = Column(Float)  # Current market probability
    mispricing_ratio = Column(Float)  # Market prob / Model prob

    # Supporting data
    mention_count = Column(Integer)  # Number of relevant mentions
    context_strength = Column(Float)  # Average confidence of mentions
    positive_mentions = Column(Integer)
    negative_mentions = Column(Integer)
    neutral_mentions = Column(Integer)

    # Analysis
    confidence_interval = Column(Float)  # Statistical confidence
    recommendation = Column(String(50))  # "buy_yes", "buy_no", "neutral"

    created_at = Column(DateTime, server_default=func.now())
    calculated_at = Column(DateTime)
