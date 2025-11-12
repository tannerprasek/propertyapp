"""Company management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_session
from app.models import Company
from app.schemas import CompanyResponse, CompanyCreate

router = APIRouter()

@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """List all tracked companies."""
    stmt = select(Company).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get company details."""
    stmt = select(Company).where(Company.id == company_id)
    result = await session.execute(stmt)
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.post("/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new company record."""
    # Check if company already exists
    stmt = select(Company).where(Company.ticker == company.ticker)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Company with this ticker already exists")

    db_company = Company(**company.model_dump())
    session.add(db_company)
    await session.commit()
    await session.refresh(db_company)
    return db_company
