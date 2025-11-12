"""Transcript management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_session
from app.models import Transcript, Company
from app.schemas import TranscriptResponse, TranscriptCreate, TranscriptDetailResponse

router = APIRouter()

@router.get("/", response_model=List[TranscriptResponse])
async def list_transcripts(
    company_id: int = None,
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    """List transcripts with optional filtering."""
    stmt = select(Transcript)
    if company_id:
        stmt = stmt.where(Transcript.company_id == company_id)
    stmt = stmt.offset(skip).limit(limit)

    result = await session.execute(stmt)
    return result.scalars().all()

@router.get("/{transcript_id}", response_model=TranscriptDetailResponse)
async def get_transcript(
    transcript_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get transcript with full details and mentions."""
    stmt = select(Transcript).where(Transcript.id == transcript_id)
    result = await session.execute(stmt)
    transcript = result.scalar_one_or_none()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return transcript

@router.post("/", response_model=TranscriptResponse)
async def create_transcript(
    transcript: TranscriptCreate,
    session: AsyncSession = Depends(get_session),
):
    """Add a new transcript."""
    # Verify company exists
    company_stmt = select(Company).where(Company.id == transcript.company_id)
    company_result = await session.execute(company_stmt)
    if not company_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Company not found")

    db_transcript = Transcript(**transcript.model_dump())
    session.add(db_transcript)
    await session.commit()
    await session.refresh(db_transcript)
    return db_transcript

@router.post("/fetch/{company_id}/all")
async def fetch_all_transcripts(company_id: int):
    """Fetch transcripts for a company from all sources."""
    return {
        "status": "fetching",
        "company_id": company_id,
        "message": "Starting transcript fetch for company"
    }

@router.post("/process/{transcript_id}")
async def process_transcript(
    transcript_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Process and clean a transcript."""
    return {
        "status": "processing",
        "transcript_id": transcript_id,
        "message": "Transcript processing started"
    }
