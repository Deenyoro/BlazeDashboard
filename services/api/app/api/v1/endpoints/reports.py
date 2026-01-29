"""API endpoints for all report data (inventory, payments, accounting, discounts, refunds, sales breakdowns)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import date
from typing import Optional, List

from app.core.database import get_db
from app.models.transaction import InventorySnapshot, DiscountUsage
from app.models.reports import (
    RefundHistory, SalesPayment, SalesByQueue, ReceivedInventory,
    InventoryReconciliation, InventoryAction, DailyAccountingSummary,
    CashDrawer, IntegratedPayment, PaymentsSnapshot
)
from app.models.sales_extended import (
    InventoryAging, InventoryDistribution, InventoryValuation,
    InventoryTransfer, SellThrough, CurrentInventory,
    SalesByCity, SalesByHour, SalesByProduct, SalesByProductCategory,
    SalesByVendor, SalesByConsumerType,
    DeliverySale, CanceledVoidSale, UncompleteSale,
    ProfitLoss, PromotionsActivity,
)

router = APIRouter()


# ============================================================================
# INVENTORY ENDPOINTS
# ============================================================================

@router.get("/inventory/snapshots")
async def list_inventory_snapshots(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    snapshot_date: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """List inventory snapshots with filtering."""
    query = select(InventorySnapshot)
    conditions = []

    if snapshot_date:
        conditions.append(InventorySnapshot.snapshot_date == snapshot_date)
    if category:
        conditions.append(InventorySnapshot.category == category)
    if search:
        conditions.append(InventorySnapshot.product_name.ilike(f"%{search}%"))

    if conditions:
        query = query.where(and_(*conditions))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Paginate
    query = query.order_by(InventorySnapshot.snapshot_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "snapshot_date": str(i.snapshot_date),
                "product_name": i.product_name,
                "sku": i.sku,
                "category": i.category,
                "brand": i.brand,
                "quantity_on_hand": i.quantity_on_hand,
                "quantity_available": i.quantity_available,
                "unit_cost": i.unit_cost,
                "total_value": i.total_value,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/inventory/actions")
async def list_inventory_actions(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    action: Optional[str] = Query(None),
):
    """List inventory actions."""
    query = select(InventoryAction)
    conditions = []

    if start_date:
        conditions.append(InventoryAction.date >= start_date)
    if end_date:
        conditions.append(InventoryAction.date <= end_date)
    if action:
        conditions.append(InventoryAction.action == action)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(InventoryAction.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "date": str(i.date),
                "product": i.product,
                "category": i.category,
                "action": i.action,
                "source": i.source,
                "quantity": i.quantity,
                "inventory_value": i.inventory_value,
                "metrc_tag": i.metrc_tag,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/inventory/reconciliation")
async def list_inventory_reconciliation(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """List inventory reconciliation records."""
    query = select(InventoryReconciliation)
    conditions = []

    if start_date:
        conditions.append(InventoryReconciliation.date >= start_date)
    if end_date:
        conditions.append(InventoryReconciliation.date <= end_date)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(InventoryReconciliation.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "date": str(i.date),
                "reconciliation_no": i.reconciliation_no,
                "product_name": i.product_name,
                "product_sku": i.product_sku,
                "category_name": i.category_name,
                "old_quantity": i.old_quantity,
                "new_quantity": i.new_quantity,
                "difference": i.difference,
                "reason": i.reason,
                "employee_name": i.employee_name,
                "cogs": i.cogs,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/inventory/received")
async def list_received_inventory(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """List received inventory/purchase orders."""
    query = select(ReceivedInventory)
    conditions = []

    if start_date:
        conditions.append(ReceivedInventory.date >= start_date)
    if end_date:
        conditions.append(ReceivedInventory.date <= end_date)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(ReceivedInventory.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "date": str(i.date) if i.date else None,
                "po_number": i.po_number,
                "po_status": i.po_status,
                "vendor": i.vendor,
                "product": i.product,
                "product_sku": i.product_sku,
                "category": i.category,
                "received_quantity": i.received_quantity,
                "unit_cost": i.unit_cost,
                "grand_total": i.grand_total,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================================
# PAYMENT ENDPOINTS
# ============================================================================

@router.get("/payments/integrated")
async def list_integrated_payments(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: Optional[str] = Query(None),
):
    """List integrated payment transactions (BlazePay, etc)."""
    query = select(IntegratedPayment)
    conditions = []

    if start_date:
        conditions.append(IntegratedPayment.transaction_completion_date >= start_date)
    if end_date:
        conditions.append(IntegratedPayment.transaction_completion_date <= end_date)
    if service:
        conditions.append(IntegratedPayment.payment_service_name.ilike(f"%{service}%"))

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(IntegratedPayment.transaction_completion_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "third_party_id": i.third_party_id,
                "payment_service_name": i.payment_service_name,
                "transaction_completion_date": str(i.transaction_completion_date) if i.transaction_completion_date else None,
                "transaction_number": i.transaction_number,
                "transaction_status": i.transaction_status,
                "customer": i.customer,
                "total_due": i.total_due,
                "paid_amount": i.paid_amount,
                "tip": i.tip,
                "payment_fee": i.payment_fee,
                "employee": i.employee,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/payments/sales")
async def list_sales_payments(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    payment_type: Optional[str] = Query(None),
):
    """List sales payment records."""
    query = select(SalesPayment)
    conditions = []

    if start_date:
        conditions.append(SalesPayment.date >= start_date)
    if end_date:
        conditions.append(SalesPayment.date <= end_date)
    if payment_type:
        conditions.append(SalesPayment.payment_type == payment_type)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(SalesPayment.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "date": str(i.date),
                "trans_no": i.trans_no,
                "trans_status": i.trans_status,
                "payment_type": i.payment_type,
                "amount_due": i.amount_due,
                "payment_tendered": i.payment_tendered,
                "tips": i.tips,
                "change_due": i.change_due,
                "shop": i.shop,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================================
# ACCOUNTING ENDPOINTS
# ============================================================================

@router.get("/accounting/daily")
async def list_daily_accounting(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """List daily accounting summaries."""
    query = select(DailyAccountingSummary)
    conditions = []

    if start_date:
        conditions.append(DailyAccountingSummary.date >= start_date)
    if end_date:
        conditions.append(DailyAccountingSummary.date <= end_date)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(DailyAccountingSummary.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "date": str(i.date),
                "shop": i.shop,
                "gross_sales": i.gross_sales,
                "net_sales": i.net_sales,
                "total_tax": i.total_tax,
                "total_due": i.total_due,
                "pre_tax_discount": i.pre_tax_discount,
                "after_tax_discount": i.after_tax_discount,
                "total_tips": i.tips,
                "total_cogs": (i.adult_cogs or 0) + (i.medical_cogs or 0) + (i.non_cannabis_cogs or 0),
                "num_transactions": i.num_transactions,
                "count_refunds": i.count_refunds,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/accounting/cash-drawers")
async def list_cash_drawers(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """List cash drawer records."""
    query = select(CashDrawer)
    conditions = []

    if start_date:
        conditions.append(CashDrawer.date >= start_date)
    if end_date:
        conditions.append(CashDrawer.date <= end_date)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(CashDrawer.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "date": str(i.date),
                "terminal": i.terminal,
                "status": i.status,
                "starting_cash": i.starting_cash,
                "ending_cash": i.ending_cash,
                "expected_in_drawer": i.expected_in_drawer,
                "actual_in_drawer": i.actual_in_drawer,
                "cash_sales": i.cash_sales,
                "cash_received": i.cash_received,
                "cash_change": i.cash_change,
                "paid_in": i.paid_in,
                "paid_out": i.paid_out,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================================
# DISCOUNTS & REFUNDS
# ============================================================================

@router.get("/discounts")
async def list_discount_usage(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    discount_name: Optional[str] = Query(None),
):
    """List discount usage records."""
    query = select(DiscountUsage)
    conditions = []

    if start_date:
        conditions.append(func.date(DiscountUsage.usage_date) >= start_date)
    if end_date:
        conditions.append(func.date(DiscountUsage.usage_date) <= end_date)
    if discount_name:
        conditions.append(DiscountUsage.discount_name.ilike(f"%{discount_name}%"))

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(DiscountUsage.usage_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "usage_date": i.usage_date.isoformat() if i.usage_date else None,
                "blaze_trans_id": i.blaze_trans_id,
                "discount_name": i.discount_name,
                "discount_type": i.discount_type,
                "discount_amount": i.discount_amount,
                "discount_percent": i.discount_percent,
                "applied_to_product": i.applied_to_product,
                "applied_by": i.applied_by,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/refunds")
async def list_refunds(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """List refund history."""
    query = select(RefundHistory)
    conditions = []

    if start_date:
        conditions.append(RefundHistory.date >= start_date)
    if end_date:
        conditions.append(RefundHistory.date <= end_date)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(RefundHistory.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "date": str(i.date),
                "trans_no": i.trans_no,
                "employee": i.employee,
                "customer": i.customer,
                "product": i.product,
                "refund_as": i.refund_as,
                "refund_amount": i.refund_amount,
                "quantity": i.quantity,
                "with_inventory": i.with_inventory,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================================
# EXTENDED INVENTORY ENDPOINTS
# ============================================================================

@router.get("/inventory/aging")
async def list_inventory_aging(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """List inventory aging data."""
    query = select(InventoryAging)
    conditions = []
    if category:
        conditions.append(InventoryAging.product_category == category)
    if search:
        conditions.append(InventoryAging.product_name.ilike(f"%{search}%"))
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
                "id": i.id, "product_sku": i.product_sku, "product_name": i.product_name,
                "product_category": i.product_category,
                "days_0_30_qty": i.days_0_30_qty, "days_0_30_val": i.days_0_30_val,
                "days_31_45_qty": i.days_31_45_qty, "days_31_45_val": i.days_31_45_val,
                "days_46_60_qty": i.days_46_60_qty, "days_46_60_val": i.days_46_60_val,
                "days_61_90_qty": i.days_61_90_qty, "days_61_90_val": i.days_61_90_val,
                "days_90_plus_qty": i.days_90_plus_qty, "days_90_plus_val": i.days_90_plus_val,
            }
            for i in items
        ],
        "total": total, "skip": skip, "limit": limit,
    }


@router.get("/inventory/distribution")
async def list_inventory_distribution(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None),
):
    """List inventory distribution by location."""
    query = select(InventoryDistribution)
    if category:
        query = query.where(InventoryDistribution.category == category)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id, "product": i.product, "category": i.category,
                "brand": i.brand, "unit_type": i.unit_type, "total": i.total,
                "exchange": i.exchange, "fulfillment": i.fulfillment,
                "quarantine": i.quarantine, "safe": i.safe, "vault": i.vault,
            }
            for i in items
        ],
        "total": total, "skip": skip, "limit": limit,
    }


@router.get("/inventory/valuation")
async def list_inventory_valuation(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None),
):
    """List inventory valuation data."""
    query = select(InventoryValuation)
    if category:
        query = query.where(InventoryValuation.category == category)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id, "product_name": i.product_name, "category": i.category,
                "status": i.status, "avg_unit_cost": i.avg_unit_cost,
                "avg_retail_price": i.avg_retail_price, "avg_profit": i.avg_profit,
                "avg_margin_pct": i.avg_margin_pct,
                "total_available_qty": i.total_available_qty,
                "total_available_cogs": i.total_available_cogs,
            }
            for i in items
        ],
        "total": total, "skip": skip, "limit": limit,
    }


@router.get("/inventory/transfers")
async def list_inventory_transfers(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """List inventory transfers."""
    query = select(InventoryTransfer)
    conditions = []
    if start_date:
        conditions.append(func.date(InventoryTransfer.date) >= start_date)
    if end_date:
        conditions.append(func.date(InventoryTransfer.date) <= end_date)
    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    query = query.order_by(InventoryTransfer.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id, "date": str(i.date) if i.date else None,
                "employee": i.employee, "product": i.product,
                "origin_shop": i.origin_shop, "origin_inventory": i.origin_inventory,
                "destination_shop": i.destination_shop, "destination": i.destination,
                "amount": i.amount,
            }
            for i in items
        ],
        "total": total, "skip": skip, "limit": limit,
    }


@router.get("/inventory/sell-through")
async def list_sell_through(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
):
    """List sell-through report data."""
    query = select(SellThrough)
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    query = query.order_by(SellThrough.days_remaining.asc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id, "product_id": i.product_id, "product_name": i.product_name,
                "category": i.category, "avg_qty_sold_per_day": i.avg_qty_sold_per_day,
                "days_remaining": i.days_remaining, "qty_on_hand": i.qty_on_hand,
            }
            for i in items
        ],
        "total": total, "skip": skip, "limit": limit,
    }


@router.get("/inventory/current")
async def list_current_inventory(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """List current inventory."""
    query = select(CurrentInventory)
    conditions = []
    if category:
        conditions.append(CurrentInventory.category == category)
    if search:
        conditions.append(CurrentInventory.product.ilike(f"%{search}%"))
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
                "id": i.id, "product": i.product, "category": i.category,
                "status": i.status, "current_quantity": i.current_quantity,
                "current_cogs": i.current_cogs, "sold_quantity": i.sold_quantity,
                "retail_price": i.retail_price, "retail_value": i.retail_value,
            }
            for i in items
        ],
        "total": total, "skip": skip, "limit": limit,
    }


# ============================================================================
# SALES BREAKDOWN ENDPOINTS
# ============================================================================

@router.get("/sales/by-city")
async def list_sales_by_city(db: AsyncSession = Depends(get_db)):
    """List sales aggregated by city."""
    result = await db.execute(
        select(SalesByCity).order_by(SalesByCity.gross_receipts.desc())
    )
    items = result.scalars().all()
    return {
        "items": [
            {
                "id": i.id, "city": i.city, "state": i.state,
                "transactions": i.transactions, "subtotal_sales": i.subtotal_sales,
                "discount": i.discount, "gross_receipts": i.gross_receipts,
                "percentage_of_sales": i.percentage_of_sales,
            }
            for i in items
        ],
        "total": len(items),
    }


@router.get("/sales/by-hour")
async def list_sales_by_hour(db: AsyncSession = Depends(get_db)):
    """List sales aggregated by hour."""
    result = await db.execute(select(SalesByHour).order_by(SalesByHour.hour))
    items = result.scalars().all()
    return {
        "items": [
            {
                "id": i.id, "hour": i.hour,
                "recreational_sales": i.recreational_sales,
                "medical_sales": i.medical_sales, "total_sales": i.total_sales,
                "gross_receipts": i.gross_receipts,
                "num_transactions": i.num_transactions,
            }
            for i in items
        ],
        "total": len(items),
    }


@router.get("/sales/by-product")
async def list_sales_by_product(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """List sales by product."""
    query = select(SalesByProduct)
    conditions = []
    if category:
        conditions.append(SalesByProduct.category == category)
    if search:
        conditions.append(or_(
            SalesByProduct.product.ilike(f"%{search}%"),
            SalesByProduct.sku.ilike(f"%{search}%"),
        ))
    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    query = query.order_by(SalesByProduct.subtotal_sales.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id, "product": i.product, "sku": i.sku,
                "category": i.category, "vendor": i.vendor, "brand": i.brand,
                "units_sold": i.units_sold, "cogs": i.cogs,
                "subtotal_sales": i.subtotal_sales, "net_sales": i.net_sales,
                "margin": i.margin, "pct_of_sales": i.pct_of_sales,
            }
            for i in items
        ],
        "total": total, "skip": skip, "limit": limit,
    }


@router.get("/sales/by-product-category")
async def list_sales_by_product_category(db: AsyncSession = Depends(get_db)):
    """List sales by product category."""
    result = await db.execute(
        select(SalesByProductCategory).order_by(SalesByProductCategory.gross_receipt.desc())
    )
    items = result.scalars().all()
    return {
        "items": [
            {
                "id": i.id, "product_category": i.product_category,
                "num_trans": i.num_trans, "cogs": i.cogs,
                "retail_value": i.retail_value, "net_sales": i.net_sales,
                "gross_receipt": i.gross_receipt, "units_sold": i.units_sold,
            }
            for i in items
        ],
        "total": len(items),
    }


@router.get("/sales/by-vendor")
async def list_sales_by_vendor(db: AsyncSession = Depends(get_db)):
    """List sales by vendor."""
    result = await db.execute(
        select(SalesByVendor).order_by(SalesByVendor.gross_receipt.desc())
    )
    items = result.scalars().all()
    return {
        "items": [
            {
                "id": i.id, "vendor": i.vendor,
                "transaction_type": i.transaction_type,
                "subtotal_sales": i.subtotal_sales,
                "discounts": i.discounts, "tax": i.tax,
                "gross_receipt": i.gross_receipt,
            }
            for i in items
        ],
        "total": len(items),
    }


@router.get("/sales/by-consumer-type")
async def list_sales_by_consumer_type(db: AsyncSession = Depends(get_db)):
    """List sales by consumer type."""
    result = await db.execute(select(SalesByConsumerType))
    items = result.scalars().all()
    return {
        "items": [
            {
                "id": i.id, "breakdown": i.breakdown,
                "cannabis_retail_value": i.cannabis_retail_value,
                "non_cannabis_retail_value": i.non_cannabis_retail_value,
                "gross_receipt": i.gross_receipt, "cogs": i.cogs,
                "net_profit": i.net_profit, "num_visits": i.num_visits,
            }
            for i in items
        ],
        "total": len(items),
    }


@router.get("/profit-loss")
async def list_profit_loss(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """List profit/loss data."""
    query = select(ProfitLoss)
    conditions = []
    if start_date:
        conditions.append(ProfitLoss.date >= start_date)
    if end_date:
        conditions.append(ProfitLoss.date <= end_date)
    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    query = query.order_by(ProfitLoss.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id, "date": str(i.date),
                "gross_receipts": i.gross_receipts, "cost": i.cost,
                "loss": i.loss, "profit": i.profit,
                "discount": i.discount, "margin_pct": i.margin_pct,
            }
            for i in items
        ],
        "total": total, "skip": skip, "limit": limit,
    }


@router.get("/promotions")
async def list_promotions_activity(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """List promotions activity."""
    query = select(PromotionsActivity)
    conditions = []
    if start_date:
        conditions.append(func.date(PromotionsActivity.date) >= start_date)
    if end_date:
        conditions.append(func.date(PromotionsActivity.date) <= end_date)
    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    query = query.order_by(PromotionsActivity.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id, "date": str(i.date) if i.date else None,
                "transaction_no": i.transaction_no,
                "promo_name": i.promo_name, "promo_type": i.promo_type,
                "cash_value": i.cash_value, "employee": i.employee,
                "member": i.member,
            }
            for i in items
        ],
        "total": total, "skip": skip, "limit": limit,
    }


@router.get("/delivery-sales")
async def list_delivery_sales(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """List delivery sales."""
    query = select(DeliverySale)
    conditions = []
    if start_date:
        conditions.append(func.date(DeliverySale.date) >= start_date)
    if end_date:
        conditions.append(func.date(DeliverySale.date) <= end_date)
    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    query = query.order_by(DeliverySale.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id, "date": str(i.date) if i.date else None,
                "transaction_id": i.transaction_id,
                "customer_first_name": i.customer_first_name,
                "customer_last_name": i.customer_last_name,
                "city": i.city, "employee": i.employee,
                "sales": i.sales, "gross_receipts": i.gross_receipts,
            }
            for i in items
        ],
        "total": total, "skip": skip, "limit": limit,
    }


@router.get("/canceled-void")
async def list_canceled_void_sales(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """List canceled/void sales."""
    query = select(CanceledVoidSale)
    conditions = []
    if start_date:
        conditions.append(func.date(CanceledVoidSale.date) >= start_date)
    if end_date:
        conditions.append(func.date(CanceledVoidSale.date) <= end_date)
    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    query = query.order_by(CanceledVoidSale.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id, "date": str(i.date) if i.date else None,
                "transaction_no": i.transaction_no, "member": i.member,
                "trans_status": i.trans_status,
                "cancellation_reason": i.cancellation_reason,
                "gross_receipt": i.gross_receipt, "employee": i.employee,
            }
            for i in items
        ],
        "total": total, "skip": skip, "limit": limit,
    }
