"""API endpoints for customer/consumer data."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.models.entities import Consumer
from app.models.members_extended import MemberPerformance, InactiveMember, MarketingContact

router = APIRouter()


@router.get("")
async def list_consumers(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    consumer_type: Optional[str] = Query(None),
):
    """List consumers with search and filtering."""
    query = select(Consumer)
    conditions = []

    if search:
        conditions.append(or_(
            Consumer.first_name.ilike(f"%{search}%"),
            Consumer.last_name.ilike(f"%{search}%"),
            Consumer.email.ilike(f"%{search}%"),
            Consumer.phone.ilike(f"%{search}%"),
        ))
    if status:
        conditions.append(Consumer.status == status)
    if consumer_type:
        conditions.append(Consumer.consumer_type == consumer_type)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(Consumer.date_joined.desc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "consumer_id": i.blaze_consumer_id,
                "first_name": i.first_name,
                "last_name": i.last_name,
                "status": i.status,
                "email": i.email,
                "phone": i.phone,
                "city": i.city,
                "state": i.state,
                "date_joined": str(i.date_joined) if i.date_joined else None,
                "consumer_type": i.consumer_type,
                "is_medical": i.is_medical,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/stats")
async def customer_stats(db: AsyncSession = Depends(get_db)):
    """Get customer summary stats."""
    total = await db.scalar(select(func.count(Consumer.id))) or 0
    active = await db.scalar(
        select(func.count(Consumer.id)).where(Consumer.status == "Accepted")
    ) or 0
    inactive_count = await db.scalar(select(func.count(InactiveMember.id))) or 0
    member_count = await db.scalar(select(func.count(MemberPerformance.id))) or 0

    return {
        "total_consumers": total,
        "active": active,
        "inactive": inactive_count,
        "members_with_performance": member_count,
    }


@router.get("/performance")
async def list_member_performance(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("gross_sales_receipts", description="Sort field"),
):
    """List member performance metrics."""
    query = select(MemberPerformance)

    if search:
        query = query.where(or_(
            MemberPerformance.member_name.ilike(f"%{search}%"),
            MemberPerformance.member_id.ilike(f"%{search}%"),
        ))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    sort_col = getattr(MemberPerformance, sort_by, MemberPerformance.gross_sales_receipts)
    query = query.order_by(sort_col.desc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "member_id": i.member_id,
                "member_name": i.member_name,
                "member_phone": i.member_phone,
                "member_group": i.member_group,
                "date_joined": str(i.date_joined) if i.date_joined else None,
                "loyalty_points": i.loyalty_points,
                "num_visits": i.num_visits,
                "num_sales": i.num_sales,
                "num_refunds": i.num_refunds,
                "gross_sales_receipts": i.gross_sales_receipts,
                "avg_sales_receipts": i.avg_sales_receipts,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/inactive")
async def list_inactive_members(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
):
    """List inactive members."""
    query = select(InactiveMember)

    if search:
        query = query.where(or_(
            InactiveMember.first_name.ilike(f"%{search}%"),
            InactiveMember.last_name.ilike(f"%{search}%"),
            InactiveMember.email.ilike(f"%{search}%"),
        ))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(InactiveMember.last_visit.desc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "first_name": i.first_name,
                "last_name": i.last_name,
                "cell_phone": i.cell_phone,
                "email": i.email,
                "last_visit": str(i.last_visit) if i.last_visit else None,
                "rec_exp_date": str(i.rec_exp_date) if i.rec_exp_date else None,
                "total_amount_spent": i.total_amount_spent,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/marketing")
async def list_marketing_contacts(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
):
    """List marketing contacts."""
    query = select(MarketingContact)
    conditions = []

    if search:
        conditions.append(or_(
            MarketingContact.first_name.ilike(f"%{search}%"),
            MarketingContact.last_name.ilike(f"%{search}%"),
            MarketingContact.email.ilike(f"%{search}%"),
        ))
    if group:
        conditions.append(MarketingContact.membership_group == group)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "first_name": i.first_name,
                "last_name": i.last_name,
                "membership_group": i.membership_group,
                "marketing_source": i.marketing_source,
                "email": i.email,
                "loyalty_points": i.loyalty_points,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }
