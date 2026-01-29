from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_, or_
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.models.transaction import Transaction, Employee
from app.models.employees_extended import EmployeePerformance, EmployeeActivity, TimeClock

router = APIRouter()


@router.get("")
async def list_employees(
    db: AsyncSession = Depends(get_db),
):
    """List employees with sales aggregates."""
    query = (
        select(
            Employee.id,
            Employee.name,
            func.count(Transaction.id).label("transaction_count"),
            func.coalesce(
                func.sum(case((Transaction.trans_type == "Sale", Transaction.total_due), else_=0)), 0
            ).label("total_sales"),
            func.coalesce(
                func.sum(case((Transaction.trans_type == "Refund", func.abs(Transaction.total_due)), else_=0)), 0
            ).label("total_refunds"),
            func.coalesce(func.sum(Transaction.total_due), 0).label("net_sales"),
            func.coalesce(
                func.avg(case((Transaction.trans_type == "Sale", Transaction.total_due), else_=None)), 0
            ).label("average_transaction"),
        )
        .select_from(Employee)
        .outerjoin(Transaction, Transaction.sold_by_name == Employee.name)
        .group_by(Employee.id, Employee.name)
        .order_by(func.sum(Transaction.total_due).desc().nulls_last())
    )

    result = await db.execute(query)
    rows = result.all()

    employees = [
        {
            "id": str(row.id),
            "employee_id": row.name,
            "name": row.name,
            "transaction_count": row.transaction_count or 0,
            "total_sales": float(row.total_sales or 0),
            "total_refunds": float(row.total_refunds or 0),
            "net_sales": float(row.net_sales or 0),
            "average_transaction": float(row.average_transaction or 0),
        }
        for row in rows
    ]

    return {"employees": employees, "total": len(employees)}


@router.get("/performance")
async def list_employee_performance(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee: Optional[str] = Query(None),
):
    """List daily employee performance metrics."""
    query = select(EmployeePerformance)
    conditions = []

    if start_date:
        conditions.append(EmployeePerformance.date >= start_date)
    if end_date:
        conditions.append(EmployeePerformance.date <= end_date)
    if employee:
        conditions.append(EmployeePerformance.employee_name.ilike(f"%{employee}%"))

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(EmployeePerformance.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "date": str(i.date) if i.date else None,
                "employee_name": i.employee_name,
                "gross_receipts": i.gross_receipts,
                "transaction_count": i.transaction_count,
                "avg_transaction": i.avg_transaction,
                "avg_transaction_time": i.avg_transaction_time,
                "promotions": i.promotions,
                "discounts": i.discounts,
                "tips": i.tips,
                "cogs": i.cogs,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/activity")
async def list_employee_activity(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
):
    """List employee activity log."""
    query = select(EmployeeActivity)
    conditions = []

    if start_date:
        conditions.append(func.date(EmployeeActivity.time) >= start_date)
    if end_date:
        conditions.append(func.date(EmployeeActivity.time) <= end_date)
    if employee:
        conditions.append(EmployeeActivity.employee.ilike(f"%{employee}%"))
    if action:
        conditions.append(EmployeeActivity.action.ilike(f"%{action}%"))

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(EmployeeActivity.time.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "time": str(i.time) if i.time else None,
                "employee": i.employee,
                "action": i.action,
                "category": i.category,
                "terminal": i.terminal,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/time-clock")
async def list_time_clock(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee: Optional[str] = Query(None),
):
    """List time clock records."""
    query = select(TimeClock)
    conditions = []

    if start_date:
        conditions.append(TimeClock.date >= start_date)
    if end_date:
        conditions.append(TimeClock.date <= end_date)
    if employee:
        conditions.append(TimeClock.employee.ilike(f"%{employee}%"))

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(TimeClock.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "date": str(i.date) if i.date else None,
                "employee": i.employee,
                "clock_in": str(i.clock_in) if i.clock_in else None,
                "terminal_in": i.terminal_in,
                "clock_out": str(i.clock_out) if i.clock_out else None,
                "terminal_out": i.terminal_out,
                "time_clocked_in": i.time_clocked_in,
                "ipad_sessions": i.ipad_sessions,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }
