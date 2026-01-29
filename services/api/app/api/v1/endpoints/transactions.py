from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
from datetime import datetime, date
from typing import Optional, List

from app.core.database import get_db
from app.models.transaction import Transaction, Member, Employee, ProductSale
from app.schemas.transaction import (
    TransactionResponse,
    TransactionListResponse,
    TransactionStats,
    SalesOverview,
    DailySales,
    ProductSaleResponse,
    TransactionDetailResponse,
)

router = APIRouter()


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    trans_type: Optional[str] = Query(None),
    trans_status: Optional[str] = Query(None),
    queue_type: Optional[str] = Query(None),
    payment_type: Optional[str] = Query(None),
    employee: Optional[str] = Query(None),
    member_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
):
    """List transactions with filtering and pagination."""
    query = select(Transaction)

    # Apply filters
    conditions = []

    if start_date:
        conditions.append(Transaction.date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        conditions.append(Transaction.date <= datetime.combine(end_date, datetime.max.time()))
    if trans_type:
        conditions.append(Transaction.trans_type == trans_type)
    if trans_status:
        conditions.append(Transaction.trans_status == trans_status)
    if queue_type:
        conditions.append(Transaction.queue_type == queue_type)
    if payment_type:
        conditions.append(Transaction.payment_type == payment_type)
    if employee:
        conditions.append(
            or_(
                Transaction.sold_by_name.ilike(f"%{employee}%"),
                Transaction.created_by_name.ilike(f"%{employee}%"),
            )
        )
    if member_id:
        conditions.append(Transaction.member_id == member_id)
    if min_amount is not None:
        conditions.append(Transaction.total_due >= min_amount)
    if max_amount is not None:
        conditions.append(Transaction.total_due <= max_amount)
    if search:
        conditions.append(
            or_(
                Transaction.trans_no.ilike(f"%{search}%"),
                Transaction.blaze_trans_id.ilike(f"%{search}%"),
            )
        )

    if conditions:
        query = query.where(and_(*conditions))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Apply pagination and ordering
    query = query.order_by(Transaction.date.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    transactions = result.scalars().all()

    return TransactionListResponse(
        transactions=[TransactionResponse.model_validate(t) for t in transactions],
        total=total or 0,
        skip=skip,
        limit=limit,
    )


@router.get("/stats", response_model=TransactionStats)
async def get_transaction_stats(
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get aggregate transaction statistics."""
    conditions = []
    if start_date:
        conditions.append(Transaction.date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        conditions.append(Transaction.date <= datetime.combine(end_date, datetime.max.time()))

    base_query = select(Transaction)
    if conditions:
        base_query = base_query.where(and_(*conditions))

    # Sales stats
    sales_query = select(
        func.count(Transaction.id).label("count"),
        func.coalesce(func.sum(Transaction.gross_sales), 0).label("gross"),
        func.coalesce(func.sum(Transaction.net_sales), 0).label("net"),
        func.coalesce(func.sum(Transaction.total_tax), 0).label("tax"),
        func.coalesce(func.sum(Transaction.tips), 0).label("tips"),
        func.coalesce(func.sum(Transaction.pre_tax_discounts), 0).label("discounts"),
        func.coalesce(func.sum(Transaction.cogs), 0).label("cogs"),
    ).where(Transaction.trans_type == "Sale")

    if conditions:
        sales_query = sales_query.where(and_(*conditions))

    sales_result = await db.execute(sales_query)
    sales = sales_result.one()

    # Refund stats
    refund_query = select(
        func.coalesce(func.sum(func.abs(Transaction.gross_sales)), 0).label("refunds")
    ).where(Transaction.trans_type == "Refund")

    if conditions:
        refund_query = refund_query.where(and_(*conditions))

    refund_result = await db.execute(refund_query)
    refunds = refund_result.scalar() or 0

    total_sales = float(sales.gross or 0)
    total_refunds = float(refunds)
    net_revenue = total_sales - total_refunds
    avg_transaction = total_sales / sales.count if sales.count > 0 else 0
    cogs = float(sales.cogs or 0)
    gross_margin = ((net_revenue - cogs) / net_revenue * 100) if net_revenue > 0 else 0

    return TransactionStats(
        total_transactions=sales.count or 0,
        total_sales=total_sales,
        total_refunds=total_refunds,
        net_revenue=net_revenue,
        total_tax_collected=float(sales.tax or 0),
        total_tips=float(sales.tips or 0),
        total_discounts=float(sales.discounts or 0),
        average_transaction=avg_transaction,
        total_cogs=cogs,
        gross_margin=round(gross_margin, 2),
    )


@router.get("/overview", response_model=SalesOverview)
async def get_sales_overview(
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get comprehensive sales overview with breakdowns."""
    conditions = []
    if start_date:
        conditions.append(Transaction.date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        conditions.append(Transaction.date <= datetime.combine(end_date, datetime.max.time()))

    # Get stats
    stats = await get_transaction_stats(db, start_date, end_date)

    # Daily breakdown - use date() for SQLite compatibility
    daily_query = select(
        func.date(Transaction.date).label("day"),
        func.count(Transaction.id).label("count"),
        func.sum(case((Transaction.trans_type == "Sale", Transaction.gross_sales), else_=0)).label("gross"),
        func.sum(case((Transaction.trans_type == "Sale", Transaction.net_sales), else_=0)).label("net"),
        func.sum(Transaction.total_tax).label("tax"),
        func.sum(Transaction.tips).label("tips"),
        func.sum(case((Transaction.trans_type == "Refund", func.abs(Transaction.gross_sales)), else_=0)).label("refunds"),
    ).group_by(func.date(Transaction.date)).order_by(func.date(Transaction.date))

    if conditions:
        daily_query = daily_query.where(and_(*conditions))

    daily_result = await db.execute(daily_query)
    daily_rows = daily_result.all()

    daily_breakdown = [
        DailySales(
            date=str(row.day) if row.day else "",
            transaction_count=row.count or 0,
            gross_sales=float(row.gross or 0),
            net_sales=float(row.net or 0),
            total_tax=float(row.tax or 0),
            tips=float(row.tips or 0),
            refunds=float(row.refunds or 0),
        )
        for row in daily_rows
    ]

    # By payment type
    payment_query = select(
        Transaction.payment_type,
        func.count(Transaction.id).label("count"),
        func.sum(Transaction.total_due).label("total"),
    ).where(Transaction.trans_type == "Sale").group_by(Transaction.payment_type)

    if conditions:
        payment_query = payment_query.where(and_(*conditions))

    payment_result = await db.execute(payment_query)
    by_payment = {
        (row.payment_type or "Unknown"): {"count": row.count, "total": float(row.total or 0)}
        for row in payment_result.all()
    }

    # By queue type
    queue_query = select(
        Transaction.queue_type,
        func.count(Transaction.id).label("count"),
        func.sum(Transaction.total_due).label("total"),
    ).where(Transaction.trans_type == "Sale").group_by(Transaction.queue_type)

    if conditions:
        queue_query = queue_query.where(and_(*conditions))

    queue_result = await db.execute(queue_query)
    by_queue = {
        (row.queue_type or "Unknown"): {"count": row.count, "total": float(row.total or 0)}
        for row in queue_result.all()
    }

    # By employee
    employee_query = select(
        Transaction.sold_by_name,
        func.count(Transaction.id).label("count"),
        func.sum(Transaction.total_due).label("total"),
    ).where(
        and_(Transaction.trans_type == "Sale", Transaction.sold_by_name.isnot(None))
    ).group_by(Transaction.sold_by_name).order_by(func.sum(Transaction.total_due).desc()).limit(10)

    if conditions:
        employee_query = employee_query.where(and_(*conditions))

    employee_result = await db.execute(employee_query)
    by_employee = {
        row.sold_by_name: {"count": row.count, "total": float(row.total or 0)}
        for row in employee_result.all()
    }

    # Top customers
    customer_query = select(
        Member.name,
        Member.blaze_member_id,
        func.count(Transaction.id).label("count"),
        func.sum(Transaction.total_due).label("total"),
    ).join(Member, Transaction.member_id == Member.id).where(
        Transaction.trans_type == "Sale"
    ).group_by(Member.id, Member.name, Member.blaze_member_id).order_by(
        func.sum(Transaction.total_due).desc()
    ).limit(10)

    if conditions:
        customer_query = customer_query.where(and_(*conditions))

    customer_result = await db.execute(customer_query)
    top_customers = [
        {
            "name": row.name or "Unknown",
            "member_id": row.blaze_member_id,
            "transactions": row.count,
            "total_spent": float(row.total or 0),
        }
        for row in customer_result.all()
    ]

    # Determine actual date range from data
    date_range_query = select(
        func.min(Transaction.date).label("min_date"),
        func.max(Transaction.date).label("max_date"),
    )
    if conditions:
        date_range_query = date_range_query.where(and_(*conditions))

    date_range_result = await db.execute(date_range_query)
    date_range = date_range_result.one()

    return SalesOverview(
        period_start=date_range.min_date or datetime.now(),
        period_end=date_range.max_date or datetime.now(),
        stats=stats,
        daily_breakdown=daily_breakdown,
        by_payment_type=by_payment,
        by_queue_type=by_queue,
        by_employee=by_employee,
        top_customers=top_customers,
    )


@router.get("/detail/{trans_no}", response_model=TransactionDetailResponse)
async def get_transaction_detail(
    trans_no: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full transaction detail including line items by transaction number."""
    # Get transaction
    result = await db.execute(
        select(Transaction).where(Transaction.trans_no == trans_no)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Get line items
    items_result = await db.execute(
        select(ProductSale)
        .where(ProductSale.trans_no == trans_no)
        .order_by(ProductSale.product_name)
    )
    items = items_result.scalars().all()

    # Get member name if we have member_id
    member_name = None
    member_group = None
    if transaction.member_id:
        member_result = await db.execute(
            select(Member).where(Member.id == transaction.member_id)
        )
        member = member_result.scalar_one_or_none()
        if member:
            member_name = member.name
            member_group = member.member_group

    # Build response
    return TransactionDetailResponse(
        id=transaction.id,
        blaze_trans_id=transaction.blaze_trans_id,
        trans_no=transaction.trans_no,
        date=transaction.date,
        created_date=transaction.created_date,
        prepared_date=transaction.prepared_date,
        packed_date=transaction.packed_date,
        shop=transaction.shop,
        company=transaction.company,
        terminal=transaction.terminal,
        region=transaction.region,
        delivery_city=transaction.delivery_city,
        trans_type=transaction.trans_type,
        trans_status=transaction.trans_status,
        queue_type=transaction.queue_type,
        order_source=transaction.order_source,
        member_name=member_name,
        member_group=member_group,
        consumer_tax_type=transaction.consumer_tax_type if hasattr(transaction, 'consumer_tax_type') else None,
        retail_value=transaction.retail_value or 0,
        gross_sales=transaction.gross_sales or 0,
        net_sales=transaction.net_sales or 0,
        net_sales_wo_fees=transaction.net_sales_wo_fees or 0,
        delivery_fees=transaction.delivery_fees or 0,
        pre_tax_discounts=transaction.pre_tax_discounts or 0,
        after_tax_discount=transaction.after_tax_discount or 0,
        product_promotions=transaction.product_promotions,
        cart_promotions=transaction.cart_promotions,
        discount_notes=transaction.discount_notes,
        pre_al_excise_tax=transaction.pre_al_excise_tax or 0,
        pre_nal_excise_tax=transaction.pre_nal_excise_tax or 0,
        city_tax=transaction.city_tax or 0,
        county_tax=transaction.county_tax or 0,
        state_tax=transaction.state_tax or 0,
        federal_tax=transaction.federal_tax or 0,
        total_tax=transaction.total_tax or 0,
        total_due=transaction.total_due or 0,
        tips=transaction.tips or 0,
        cogs=transaction.cogs or 0,
        payment_type=transaction.payment_type,
        blazepay_id=transaction.blazepay_id,
        payment_tendered=transaction.payment_tendered or 0,
        cash_change=transaction.cash_change or 0,
        change_due=transaction.change_due or 0,
        sold_by_name=transaction.sold_by_name,
        created_by_name=transaction.created_by_name,
        prepared_by=transaction.prepared_by,
        packed_by=transaction.packed_by,
        marketing_source=transaction.marketing_source,
        order_tags=transaction.order_tags,
        loyalty_points_spent=transaction.loyalty_points_spent or 0,
        loyalty_points_earned=transaction.loyalty_points_earned or 0,
        compliance_system=transaction.compliance_system,
        compliance_order_id=transaction.compliance_order_id,
        items=[ProductSaleResponse.model_validate(item) for item in items],
        item_count=len(items),
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single transaction by ID."""
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return TransactionResponse.model_validate(transaction)


@router.get("/blaze/{blaze_trans_id}", response_model=TransactionResponse)
async def get_transaction_by_blaze_id(
    blaze_trans_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single transaction by Blaze transaction ID."""
    result = await db.execute(
        select(Transaction).where(Transaction.blaze_trans_id == blaze_trans_id)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return TransactionResponse.model_validate(transaction)
