"""API endpoints for product catalog, batches, vendors."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.models.entities import ProductCatalog, ProductBatch, Vendor
from app.models.sales_extended import (
    ProductsByVendor, ProductSellByExpire, SalesByProduct,
)

router = APIRouter()


@router.get("")
async def list_products(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
):
    """List products from the product catalog."""
    query = select(ProductCatalog)
    conditions = []

    if search:
        conditions.append(or_(
            ProductCatalog.item.ilike(f"%{search}%"),
            ProductCatalog.sku.ilike(f"%{search}%"),
        ))
    if category:
        conditions.append(ProductCatalog.category == category)
    if brand:
        conditions.append(ProductCatalog.brand == brand)
    if vendor:
        conditions.append(ProductCatalog.vendor.ilike(f"%{vendor}%"))
    if active is not None:
        conditions.append(ProductCatalog.active == active)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(ProductCatalog.item).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "sku": i.sku,
                "item": i.item,
                "category": i.category,
                "brand": i.brand,
                "vendor": i.vendor,
                "unit_price": i.unit_price,
                "cost_per_unit": i.cost_per_unit,
                "cannabis": i.cannabis,
                "cannabis_type": i.cannabis_type,
                "strain": i.strain,
                "thc_pct": i.thc_pct,
                "cbd_pct": i.cbd_pct,
                "inventory_available": i.inventory_available,
                "active": i.active,
                "available_online": i.available_online,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/stats")
async def product_stats(db: AsyncSession = Depends(get_db)):
    """Get product catalog summary stats."""
    total = await db.scalar(select(func.count(ProductCatalog.id))) or 0
    categories = await db.scalar(
        select(func.count(func.distinct(ProductCatalog.category)))
    ) or 0
    vendors_count = await db.scalar(select(func.count(Vendor.id))) or 0
    batches = await db.scalar(select(func.count(ProductBatch.id))) or 0
    active = await db.scalar(
        select(func.count(ProductCatalog.id)).where(ProductCatalog.active == True)
    ) or 0

    return {
        "total_products": total,
        "active_products": active,
        "categories": categories,
        "vendors": vendors_count,
        "batches": batches,
    }


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List distinct product categories."""
    result = await db.execute(
        select(ProductCatalog.category, func.count(ProductCatalog.id).label("count"))
        .where(ProductCatalog.category.isnot(None))
        .group_by(ProductCatalog.category)
        .order_by(func.count(ProductCatalog.id).desc())
    )
    return {"categories": [{"name": r[0], "count": r[1]} for r in result.all()]}


@router.get("/batches")
async def list_batches(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """List product batches."""
    query = select(ProductBatch)
    conditions = []

    if search:
        conditions.append(or_(
            ProductBatch.product_name.ilike(f"%{search}%"),
            ProductBatch.product_sku.ilike(f"%{search}%"),
            ProductBatch.batch_id.ilike(f"%{search}%"),
        ))
    if category:
        conditions.append(ProductBatch.category == category)
    if status:
        conditions.append(ProductBatch.status == status)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(ProductBatch.received_date.desc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "product_name": i.product_name,
                "product_sku": i.product_sku,
                "batch_id": i.batch_id,
                "category": i.category,
                "brand": i.brand,
                "vendor_name": i.vendor_name,
                "status": i.status,
                "purchased_qty": i.purchased_qty,
                "current_qty": i.current_qty,
                "cost_per_unit": i.cost_per_unit,
                "total_thc_pct": i.total_thc_pct,
                "total_cbd_pct": i.total_cbd_pct,
                "received_date": str(i.received_date) if i.received_date else None,
                "sell_by_date": str(i.sell_by_date) if i.sell_by_date else None,
                "expiration_date": str(i.expiration_date) if i.expiration_date else None,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/vendors")
async def list_vendors(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
):
    """List vendors."""
    query = select(Vendor)
    conditions = []

    if search:
        conditions.append(Vendor.vendor_name.ilike(f"%{search}%"))
    if active is not None:
        conditions.append(Vendor.active == active)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(Vendor.vendor_name).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "vendor_name": i.vendor_name,
                "contact_first_name": i.contact_first_name,
                "contact_last_name": i.contact_last_name,
                "phone": i.phone,
                "email": i.email,
                "active": i.active,
                "city": i.city,
                "state": i.state,
                "vendor_type": i.vendor_type,
                "license_number": i.license_number,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/by-vendor")
async def list_products_by_vendor(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    vendor: Optional[str] = Query(None),
):
    """List products grouped by vendor with stock/sales info."""
    query = select(ProductsByVendor)

    if vendor:
        query = query.where(ProductsByVendor.vendor.ilike(f"%{vendor}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(ProductsByVendor.vendor, ProductsByVendor.product).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "vendor": i.vendor,
                "contact_first_name": i.contact_first_name,
                "contact_surname": i.contact_surname,
                "category": i.category,
                "brand": i.brand,
                "product": i.product,
                "quantity_sold": i.quantity_sold,
                "quantity_in_stock": i.quantity_in_stock,
                "sales": i.sales,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/sell-by-expire")
async def list_sell_by_expire(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None),
):
    """List products by sell-by/expiration date."""
    query = select(ProductSellByExpire)

    if category:
        query = query.where(ProductSellByExpire.product_category == category)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(ProductSellByExpire.sell_by_date.asc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "product_category": i.product_category,
                "product_name": i.product_name,
                "status": i.status,
                "batch_id": i.batch_id,
                "sell_by_date": str(i.sell_by_date) if i.sell_by_date else None,
                "qty_remaining": i.qty_remaining,
                "low_inventory_threshold": i.low_inventory_threshold,
                "unit_type": i.unit_type,
            }
            for i in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }
