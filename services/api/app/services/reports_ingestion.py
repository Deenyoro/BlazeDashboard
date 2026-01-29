"""
Comprehensive ingestion service for all Blaze report types.

This module handles ingestion for:
- refund_history_report.csv
- sales_payments_report.csv
- sales_by_queue_insights.csv
- received_inventory.csv
- inventory_snapshot_report_insights.csv
- inventory_reconciliation_history_insights.csv
- inventory_action_summary.csv
- daily_accounting_summary.csv
- cash_drawer_insights.csv
- unified_discount.csv
- integrated_payments_report.csv
- payments_snapshot.csv
"""

import pandas as pd
from datetime import datetime, date as date_type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Dict, Any, Set
import logging
import hashlib
import os

from app.models.reports import (
    RefundHistory, SalesPayment, SalesByQueue, ReceivedInventory,
    InventoryReconciliation, InventoryAction, DailyAccountingSummary,
    CashDrawer, IntegratedPayment, PaymentsSnapshot
)
from app.models.transaction import InventorySnapshot, DiscountUsage

logger = logging.getLogger(__name__)

# Base data directory - can be overridden by environment variable
DATA_DIR = os.environ.get("DATA_DIR", "/app/data")

# CSV file locations - all flat in DATA_DIR
CSV_PATHS = {
    "total_sales": f"{DATA_DIR}/total_sales.csv",
    "sales_details": f"{DATA_DIR}/completed_sales_details_report.csv",
    "refund_history": f"{DATA_DIR}/refund_history_report.csv",
    "sales_by_queue": f"{DATA_DIR}/sales_by_queue_insights.csv",
    "inventory_snapshot": f"{DATA_DIR}/inventory_snapshot_report_insights.csv",
    "inventory_reconciliation": f"{DATA_DIR}/inventory_reconciliation_history_insights.csv",
    "inventory_actions": f"{DATA_DIR}/inventory_action_summary.csv",
    "received_inventory": f"{DATA_DIR}/received_inventory.csv",
    "sales_payments": f"{DATA_DIR}/sales_payments_report.csv",
    "integrated_payments": f"{DATA_DIR}/integrated_payments_report.csv",
    "payments_snapshot": f"{DATA_DIR}/payments_snapshot.csv",
    "daily_accounting": f"{DATA_DIR}/daily_accounting_summary.csv",
    "cash_drawer": f"{DATA_DIR}/cash_drawer_insights.csv",
    "discount_usage": f"{DATA_DIR}/unified_discount.csv",
}

# Extended CSV paths for new report types (imported by other ingestion modules)
CSV_PATHS_EXTENDED = {
    # Entities
    "vendors": f"{DATA_DIR}/vendors_export.csv",
    "product_catalog": f"{DATA_DIR}/company_products_export.csv",
    "product_batches": f"{DATA_DIR}/company_product_batch_export.csv",
    "consumers": f"{DATA_DIR}/consumer_export.csv",
    # Employees
    "employee_performance": f"{DATA_DIR}/master_employee_report.csv",
    "employee_activity": f"{DATA_DIR}/employee_activity.csv",
    "time_clock": f"{DATA_DIR}/time_clock_reports.csv",
    # Members
    "member_performance": f"{DATA_DIR}/member_performance.csv",
    "inactive_members": f"{DATA_DIR}/inactive_members.csv",
    "marketing": f"{DATA_DIR}/marketing.csv",
    # Extended sales
    "delivery_sales": f"{DATA_DIR}/delivery_sales.csv",
    "canceled_void_sales": f"{DATA_DIR}/total_sales_canceled_void_orders.csv",
    "uncomplete_sales": f"{DATA_DIR}/total_sales_with_uncomplete_orders.csv",
    "promotions_activity": f"{DATA_DIR}/promotions_activity.csv",
    "profit_loss": f"{DATA_DIR}/profit_loss_report.csv",
    "purchase_order_by_category": f"{DATA_DIR}/purchase_order_by_category.csv",
    "return_to_vendor": f"{DATA_DIR}/return_to_vendor.csv",
    "refund_history_detail": f"{DATA_DIR}/refund_history.csv",
    "paidinout_activity": f"{DATA_DIR}/paidinout_activity.csv",
    # Inventory extended
    "inventory_aging": f"{DATA_DIR}/inventory_aging.csv",
    "inventory_distribution": f"{DATA_DIR}/inventory_distribution.csv",
    "inventory_valuation": f"{DATA_DIR}/inventory_log_valuation.csv",
    "inventory_transfers": f"{DATA_DIR}/inventory_transfer_log.csv",
    "sell_through": f"{DATA_DIR}/sell_through_report.csv",
    "current_inventory": f"{DATA_DIR}/single_inventory.csv",
    # Sales breakdowns
    "sales_by_city": f"{DATA_DIR}/sales_by_city.csv",
    "sales_by_consumer_type": f"{DATA_DIR}/sales_by_consumer_type.csv",
    "sales_by_hour": f"{DATA_DIR}/sales_by_hour.csv",
    "sales_by_product": f"{DATA_DIR}/sales_by_product.csv",
    "sales_by_product_category": f"{DATA_DIR}/sales_by_product_category.csv",
    "sales_by_vendor": f"{DATA_DIR}/sales_by_vendor.csv",
    "employee_sales_by_product": f"{DATA_DIR}/employee_by_sales_by_product.csv",
    "products_by_vendor": f"{DATA_DIR}/products_by_vendor.csv",
    "product_sales_by_inventory": f"{DATA_DIR}/product_sales_by_inventory.csv",
    "product_sell_by_expire": f"{DATA_DIR}/product_sell_by_expire.csv",
}


def get_csv_path(report_type: str, custom_path: str = None) -> Optional[str]:
    """Get the path to a CSV file, checking multiple locations."""
    if custom_path and os.path.exists(custom_path):
        return custom_path

    # Try the organized path first
    if report_type in CSV_PATHS:
        if os.path.exists(CSV_PATHS[report_type]):
            return CSV_PATHS[report_type]

    return None


def parse_datetime(val) -> Optional[datetime]:
    """Parse datetime from CSV."""
    if pd.isna(val) or val == "" or val is None:
        return None
    try:
        if isinstance(val, datetime):
            return val
        val_str = str(val)
        if "1969-12-31" in val_str or "1970-01-01" in val_str or "1900" in val_str:
            return None
        # Handle timestamps with colon-separated milliseconds (e.g., "01/23/2026 15:06:42:343")
        import re
        ms_match = re.match(r'^(.+:\d{2}):(\d{3})$', val_str)
        if ms_match:
            val_str = ms_match.group(1) + '.' + ms_match.group(2)
        return pd.to_datetime(val_str)
    except Exception:
        return None


def parse_date(val) -> Optional[date_type]:
    """Parse date from CSV."""
    dt = parse_datetime(val)
    return dt.date() if dt else None


def parse_float(val) -> float:
    """Parse float from CSV."""
    if pd.isna(val) or val == "" or val is None:
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace("$", "").replace(",", "").strip()
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def parse_int(val) -> int:
    """Parse int from CSV."""
    if pd.isna(val) or val == "" or val is None:
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def parse_str(val) -> Optional[str]:
    """Parse string from CSV."""
    if pd.isna(val) or val == "" or val is None:
        return None
    return str(val).strip()


def parse_bool(val, true_val="Yes") -> bool:
    """Parse boolean from CSV."""
    if pd.isna(val):
        return False
    s = str(val).strip().lower()
    return s == true_val.lower() or s == "true" or s == "t" or s == "1"


def generate_hash(*args) -> str:
    """Generate a SHA256 hash from arguments."""
    hash_string = "|".join(str(a) for a in args)
    return hashlib.sha256(hash_string.encode()).hexdigest()


async def get_existing_hashes(db: AsyncSession, model, hash_field: str) -> Set[str]:
    """Get existing hash values from a model."""
    result = await db.execute(select(getattr(model, hash_field)))
    return {row[0] for row in result.all() if row[0]}


# ============================================================================
# REFUND HISTORY INGESTION
# ============================================================================

async def ingest_refund_history(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest refund_history_report.csv."""
    final_path = get_csv_path("refund_history", csv_path)
    if not final_path:
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting refund history from {final_path}")

    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)
    logger.info(f"CSV loaded: {total_rows} rows")

    existing_hashes = await get_existing_hashes(db, RefundHistory, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                continue

            # Column name in this CSV is "Trans No" (no period)
            trans_no = parse_str(row.get('Trans No'))
            line_hash = generate_hash(
                date_val, trans_no, row.get('Product'),
                row.get('Refund Amount'), row.get('Quantity')
            )

            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = RefundHistory(
                line_hash=line_hash,
                date=date_val,
                trans_no=trans_no,
                employee=parse_str(row.get('Employee')),
                customer=parse_str(row.get('Customer')),
                with_inventory=parse_bool(row.get('WithInventory')),
                product=parse_str(row.get('Product')),
                refund_as=parse_str(row.get('Refund As')),
                item_price=parse_float(row.get('Item Price')),
                refund_amount=parse_float(row.get('Refund Amount')),
                quantity=parse_float(row.get('Quantity')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(RefundHistory.id)))

    return {
        "table": "refund_history",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped,
        "total_in_db": final_count
    }


# ============================================================================
# SALES PAYMENTS INGESTION
# ============================================================================

async def ingest_sales_payments(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest sales_payments_report.csv."""
    final_path = get_csv_path("sales_payments", csv_path)
    if not final_path:
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting sales payments from {final_path}")

    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, SalesPayment, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                continue

            line_hash = generate_hash(
                row.get('Trans No'), date_val, row.get('Payment Type'),
                row.get('Amount Due'), row.get('Payment Tendered')
            )

            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = SalesPayment(
                line_hash=line_hash,
                trans_no=parse_str(row.get('Trans No')),
                trans_status=parse_str(row.get('Trans Status')),
                date=date_val,
                company=parse_str(row.get('Company')),
                shop=parse_str(row.get('Shop')),
                payment_type=parse_str(row.get('Payment Type')),
                amount_due=parse_float(row.get('Amount Due')),
                cash_back=parse_float(row.get('Cash Back')),
                tips=parse_float(row.get('Tips')),
                change_due=parse_float(row.get('Change Due')),
                payment_tendered=parse_float(row.get('Payment Tendered')),
                payment_fee=parse_float(row.get('Payment Fee')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(SalesPayment.id)))

    return {
        "table": "sales_payments",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped,
        "total_in_db": final_count
    }


# ============================================================================
# SALES BY QUEUE INGESTION
# ============================================================================

async def ingest_sales_by_queue(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest sales_by_queue_insights.csv."""
    final_path = get_csv_path("sales_by_queue", csv_path)
    if not final_path:
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting sales by queue from {final_path}")

    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, SalesByQueue, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                continue

            line_hash = generate_hash(
                date_val, row.get('Shop'), row.get('Queue Type')
            )

            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = SalesByQueue(
                line_hash=line_hash,
                date=date_val,
                shop=parse_str(row.get('Shop')),
                company=parse_str(row.get('Company')),
                queue_type=parse_str(row.get('Queue Type')),
                total_due=parse_float(row.get('Total Due')),
                net_sales=parse_float(row.get('Net Sales')),
                net_sales_wo_fees=parse_float(row.get('Net Sales w/o Fees')),
                num_completed_transactions=parse_int(row.get('Number of Completed Transactions')),
                num_refunds=parse_int(row.get('Number of Refunds')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(SalesByQueue.id)))

    return {
        "table": "sales_by_queue",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped,
        "total_in_db": final_count
    }


# ============================================================================
# RECEIVED INVENTORY INGESTION
# ============================================================================

async def ingest_received_inventory(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest received_inventory.csv."""
    final_path = get_csv_path("received_inventory", csv_path)
    if not final_path:
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting received inventory from {final_path}")

    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, ReceivedInventory, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                continue

            line_hash = generate_hash(
                date_val, row.get('PO Number'), row.get('Product SKU'),
                row.get('METRC Tag'), row.get('Received Quantity')
            )

            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = ReceivedInventory(
                line_hash=line_hash,
                company=parse_str(row.get('Company')),
                shop=parse_str(row.get('Shop')),
                date=date_val,
                completed_date=parse_date(row.get('Completed Date')),
                delivery_date=parse_date(row.get('Delivery Date')),
                received_date=parse_date(row.get('Received Date')),
                approved_date=parse_date(row.get('Approved Date')),
                po_date=parse_date(row.get('PO Date')),
                po_number=parse_str(row.get('PO Number')),
                po_status=parse_str(row.get('PO Status')),
                transaction_type=parse_str(row.get('Transaction Type')),
                sb_number=parse_str(row.get('SB Number')),
                payment_status=parse_str(row.get('Payment Status')),
                reference=parse_str(row.get('Reference')),
                unique_id=parse_str(row.get('Unique ID')),
                product_sku=parse_str(row.get('Product SKU')),
                product=parse_str(row.get('Product')),
                brand=parse_str(row.get('Brand')),
                category=parse_str(row.get('Category')),
                vendor=parse_str(row.get('Vendor')),
                metrc_tag=parse_str(row.get('METRC Tag')),
                paid_amount=parse_float(row.get('Paid Amount')),
                unpaid_amount=parse_float(row.get('Unpaid Amount')),
                unit_cost=parse_float(row.get('Unit Cost')),
                request_quantity=parse_float(row.get('Request Quantity')),
                received_quantity=parse_float(row.get('Received Quantity')),
                request_total_cost=parse_float(row.get('Request Total Cost')),
                received_total_cost=parse_float(row.get('Received Total Cost')),
                final_total_cost=parse_float(row.get('Final Total Cost')),
                excise_tax=parse_float(row.get('Excise Tax')),
                discount=parse_float(row.get('Discount')),
                adjustment_amount=parse_float(row.get('Adjustment Amount')),
                fees=parse_float(row.get('Fees')),
                grand_total=parse_float(row.get('Grand Total')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(ReceivedInventory.id)))

    return {
        "table": "received_inventory",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped,
        "total_in_db": final_count
    }


# ============================================================================
# INVENTORY SNAPSHOT INGESTION
# ============================================================================

async def ingest_inventory_snapshot(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest inventory_snapshot_report_insights.csv."""
    final_path = get_csv_path("inventory_snapshot", csv_path)
    if not final_path:
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting inventory snapshot from {final_path}")

    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)

    # Get existing snapshots (date + sku + unique_id)
    result = await db.execute(
        select(InventorySnapshot.snapshot_date, InventorySnapshot.sku, InventorySnapshot.blaze_product_id)
    )
    existing = {(str(r[0]), r[1], r[2]) for r in result.all()}
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                continue

            sku = parse_str(row.get('Product SKU'))
            unique_id = parse_str(row.get('Unique ID'))
            key = (str(date_val), sku, unique_id)

            if key in existing:
                skipped += 1
                continue

            record = InventorySnapshot(
                snapshot_date=date_val,
                blaze_product_id=unique_id,
                sku=sku,
                product_name=parse_str(row.get('Product Name')) or "Unknown",
                category=parse_str(row.get('Product Category')),
                brand=parse_str(row.get('Brand')),
                quantity_on_hand=parse_float(row.get('Quantity on Hand')),
                quantity_available=parse_float(row.get('Quantity on Hand')),
                quantity_reserved=0.0,
                unit_cost=parse_float(row.get('Unit Cost')),
                total_value=parse_float(row.get('Inventory Value')),
            )
            db.add(record)
            existing.add(key)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(InventorySnapshot.id)))

    return {
        "table": "inventory_snapshots",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped,
        "total_in_db": final_count
    }


# ============================================================================
# INVENTORY RECONCILIATION INGESTION
# ============================================================================

async def ingest_inventory_reconciliation(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest inventory_reconciliation_history_insights.csv."""
    final_path = get_csv_path("inventory_reconciliation", csv_path)
    if not final_path:
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting inventory reconciliation from {final_path}")

    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, InventoryReconciliation, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                continue

            # Handle column name variations
            metrc_tag = parse_str(row.get('METRC Tag')) or parse_str(row.get('Metrc Tag'))

            line_hash = generate_hash(
                row.get('Date Timestamp'), row.get('Reconciliation No'),
                row.get('Product SKU'), metrc_tag,
                row.get('New Quantity'), row.get('Old Quantity')
            )

            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = InventoryReconciliation(
                line_hash=line_hash,
                date=date_val,
                date_timestamp=parse_datetime(row.get('Date Timestamp')),
                shop=parse_str(row.get('Shop')),
                company=parse_str(row.get('Company')),
                reconciliation_no=parse_str(row.get('Reconciliation No')),
                employee_name=parse_str(row.get('Employee Name')),
                inventory_name=parse_str(row.get('Inventory Name')),
                product_name=parse_str(row.get('Product Name')),
                brand_name=parse_str(row.get('Brand Name')),
                product_sku=parse_str(row.get('Product SKU')),
                category_name=parse_str(row.get('Category Name')),
                batch_sku=parse_str(row.get('Batch SKU')),
                metrc_tag=metrc_tag,
                new_quantity=parse_float(row.get('New Quantity')),
                old_quantity=parse_float(row.get('Old Quantity')),
                difference=parse_float(row.get('Difference')),
                report_loss=parse_bool(row.get('Report Loss')),
                metrc_adjustment=parse_str(row.get('Metrc Adjustment')),
                low_inventory_threshold=parse_float(row.get('Low Inventory Threshold')),
                cost_per_unit=parse_float(row.get('Cost per Unit')),
                cogs=parse_float(row.get('COGS')),
                pre_package_name=parse_str(row.get('Pre Package Name')),
                reason=parse_str(row.get('Reason')),
                reason_note=parse_str(row.get('Reason Note')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(InventoryReconciliation.id)))

    return {
        "table": "inventory_reconciliation",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped,
        "total_in_db": final_count
    }


# ============================================================================
# INVENTORY ACTIONS INGESTION
# ============================================================================

async def ingest_inventory_actions(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest inventory_action_summary.csv."""
    final_path = get_csv_path("inventory_actions", csv_path)
    if not final_path:
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting inventory actions from {final_path}")

    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, InventoryAction, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                continue

            # Column names may vary: "Unique Id" or "Unique ID"
            unique_id = parse_str(row.get('Unique Id')) or parse_str(row.get('Unique ID'))
            metrc_tag = parse_str(row.get('METRC Tag')) or parse_str(row.get('Metrc Tag'))

            line_hash = generate_hash(
                date_val, unique_id, metrc_tag,
                row.get('Action'), row.get('Quantity'), row.get('Inventory Value')
            )

            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = InventoryAction(
                line_hash=line_hash,
                date=date_val,
                unique_id=unique_id,
                metrc_tag=metrc_tag,
                product=parse_str(row.get('Product')),
                category=parse_str(row.get('Category')),
                source=parse_str(row.get('Source')),
                action=parse_str(row.get('Action')),
                quantity=parse_float(row.get('Quantity')),
                inventory_value=parse_float(row.get('Inventory Value')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(InventoryAction.id)))

    return {
        "table": "inventory_actions",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped,
        "total_in_db": final_count
    }


# ============================================================================
# DAILY ACCOUNTING SUMMARY INGESTION
# ============================================================================

async def ingest_daily_accounting(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest daily_accounting_summary.csv."""
    final_path = get_csv_path("daily_accounting", csv_path)
    if not final_path:
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting daily accounting from {final_path}")

    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, DailyAccountingSummary, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                continue

            line_hash = generate_hash(
                date_val, row.get('Shop'), row.get('Queue Type')
            )

            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = DailyAccountingSummary(
                line_hash=line_hash,
                date=date_val,
                shop=parse_str(row.get('Shop')),
                company=parse_str(row.get('Company')),
                queue_type=parse_str(row.get('Queue Type')),
                adult_retail_value=parse_float(row.get('Adult Retail Value of Sales')),
                medical_retail_value=parse_float(row.get('Medical Retail Value of Sales')),
                non_cannabis_retail_value=parse_float(row.get('Non-Cannabis Retail Value of Sales')),
                retail_value_of_sales=parse_float(row.get('Retail Value of Sales')),
                gross_sales=parse_float(row.get('Gross Sales')),
                net_sales=parse_float(row.get('Net Sales')),
                net_sales_wo_fees=parse_float(row.get('Net Sales w/o Fees')),
                total_tax=parse_float(row.get('Total Tax')),
                total_due=parse_float(row.get('Total Due')),
                tips=parse_float(row.get('Tips')),
                blazepay_tips=parse_float(row.get('BLAZEPAY Tips')),
                num_transactions=parse_int(row.get('Number of Transactions')),
                count_completed_sales=parse_int(row.get('Count of Completed Sales')),
                count_refunds=parse_int(row.get('Count of Refunds')),
                new_members=parse_int(row.get('New Members')),
                returning_members=parse_int(row.get('Returning Members')),
                adult_cogs=parse_float(row.get('Adult COGS')),
                medical_cogs=parse_float(row.get('Medical COGS')),
                non_cannabis_cogs=parse_float(row.get('Non-Cannabis COGS')),
                cash_tendered=parse_float(row.get('Cash Tendered')),
                blazepay_tendered=parse_float(row.get('BLAZEPay Tendered')),
                payment_tendered=parse_float(row.get('Payment Tendered')),
                change_due=parse_float(row.get('Change Due')),
                items_sold=parse_int(row.get('Items Sold')),
                items_refunded=parse_int(row.get('Items Refunded')),
                refund_total_due=parse_float(row.get('Refund Total Due')),
                blazepay_cashback=parse_float(row.get('BLAZEPay Cashback')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(DailyAccountingSummary.id)))

    return {
        "table": "daily_accounting_summary",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped,
        "total_in_db": final_count
    }


# ============================================================================
# CASH DRAWER INGESTION
# ============================================================================

async def ingest_cash_drawer(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest cash_drawer_insights.csv."""
    final_path = get_csv_path("cash_drawer", csv_path)
    if not final_path:
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting cash drawer from {final_path}")

    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, CashDrawer, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                continue

            line_hash = generate_hash(
                date_val, row.get('Terminal'), row.get('Start Time'), row.get('End Time')
            )

            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = CashDrawer(
                line_hash=line_hash,
                date=date_val,
                terminal=parse_str(row.get('Terminal')),
                status=parse_str(row.get('Status')),
                start_time=parse_datetime(row.get('Start Time')),
                end_time=parse_datetime(row.get('End Time')),
                starting_cash=parse_float(row.get('Starting Cash')),
                ending_cash=parse_float(row.get('Ending Cash')),
                paid_in=parse_float(row.get('Paid In')),
                paid_out=parse_float(row.get('Paid Out')),
                cash_drops=parse_float(row.get('Cash Drops')),
                expected_in_drawer=parse_float(row.get('Expected in Drawer')),
                actual_in_drawer=parse_float(row.get('Actual in Drawer')),
                cash_sales=parse_float(row.get('Cash Sales')),
                check_sales=parse_float(row.get('Check Sales')),
                credit_sales=parse_float(row.get('Credit Sales')),
                store_credit_sales=parse_float(row.get('Store Credit Sales')),
                blazepay_sales=parse_float(row.get('BlazePay Sales')),
                ach_sales=parse_float(row.get('ACH Sales')),
                gift_card_sales=parse_float(row.get('Gift Card Sales')),
                cashless_atm_sales=parse_float(row.get('CashlessAtm Sales')),
                cash_received=parse_float(row.get('Cash Received')),
                cashless_atm_received=parse_float(row.get('CashlessAtm Received')),
                cash_change=parse_float(row.get('Cash Change')),
                cashless_atm_change=parse_float(row.get('CashlessAtm Change')),
                cash_refunds=parse_float(row.get('Cash Refunds')),
                blazepay_refunds=parse_float(row.get('BlazePay Refunds')),
                blazepay_cashback=parse_float(row.get('BlazePay Cashback')),
                blazepay_tips=parse_float(row.get('BlazePay Tips')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(CashDrawer.id)))

    return {
        "table": "cash_drawers",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped,
        "total_in_db": final_count
    }


# ============================================================================
# DISCOUNT USAGE INGESTION
# ============================================================================

async def ingest_discount_usage(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest unified_discount.csv."""
    final_path = get_csv_path("discount_usage", csv_path)
    if not final_path:
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting discount usage from {final_path}")

    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)

    # Get existing (trans_no + discount_name combo)
    result = await db.execute(
        select(DiscountUsage.blaze_trans_id, DiscountUsage.discount_name)
    )
    existing = {(r[0], r[1]) for r in result.all()}
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_datetime(row.get('Date'))
            if not date_val:
                continue

            trans_no = parse_str(row.get('Trans No'))
            discount_name = parse_str(row.get('Promotion Name'))

            if not trans_no or not discount_name:
                continue

            key = (trans_no, discount_name)
            if key in existing:
                skipped += 1
                continue

            record = DiscountUsage(
                blaze_trans_id=trans_no,
                usage_date=date_val,
                discount_name=discount_name,
                discount_type=parse_str(row.get('Promotion Type')),
                discount_amount=parse_float(row.get('Discounted Amount')),
            )
            db.add(record)
            existing.add(key)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(DiscountUsage.id)))

    return {
        "table": "discount_usage",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped,
        "total_in_db": final_count
    }


# ============================================================================
# INTEGRATED PAYMENTS INGESTION
# ============================================================================

async def ingest_integrated_payments(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest integrated_payments_report.csv."""
    final_path = get_csv_path("integrated_payments", csv_path)
    if not final_path:
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting integrated payments from {final_path}")

    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)

    # Get existing 3rd party IDs
    result = await db.execute(select(IntegratedPayment.third_party_id))
    existing = {r[0] for r in result.all() if r[0]}
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            third_party_id = parse_str(row.get('3rd Party ID'))
            if not third_party_id:
                continue

            if third_party_id in existing:
                skipped += 1
                continue

            record = IntegratedPayment(
                third_party_id=third_party_id,
                payment_service_name=parse_str(row.get('Payment Service Name')),
                processed_time=parse_datetime(row.get('Processed Time')),
                transaction_completion_date=parse_date(row.get('Transaction Completion Date')),
                transaction_number=parse_str(row.get('Transaction Number')),
                transaction_status=parse_str(row.get('Transaction Status')),
                customer=parse_str(row.get('Customer')),
                total_due=parse_float(row.get('Total Due')),
                paid_amount=parse_float(row.get('Paid Amount')),
                tip=parse_float(row.get('Tip')),
                cashback=parse_float(row.get('Cashback')),
                payment_fee=parse_float(row.get('Payment Fee')),
                gross_payment=parse_float(row.get('Gross Payment')),
                employee=parse_str(row.get('Employee')),
                terminal_id=parse_str(row.get('Terminal ID')),
                terminal_name=parse_str(row.get('Terminal Name')),
                third_party_terminal_id=parse_str(row.get('3rd Party Terminal ID')),
                payment_id=parse_str(row.get('Payment ID')),
            )
            db.add(record)
            existing.add(third_party_id)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(IntegratedPayment.id)))

    return {
        "table": "integrated_payments",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped,
        "total_in_db": final_count
    }


# ============================================================================
# PAYMENTS SNAPSHOT INGESTION
# ============================================================================

async def ingest_payments_snapshot(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest payments_snapshot.csv."""
    final_path = get_csv_path("payments_snapshot", csv_path)
    if not final_path:
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting payments snapshot from {final_path}")

    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, PaymentsSnapshot, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                continue

            line_hash = generate_hash(
                date_val, row.get('Shop'), row.get('Payment Type'),
                row.get('Queue Type'), row.get('Total Due')
            )

            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = PaymentsSnapshot(
                line_hash=line_hash,
                date=date_val,
                shop=parse_str(row.get('Shop')),
                company=parse_str(row.get('Company')),
                payment_type=parse_str(row.get('Payment Type')),
                payment_type_usage=parse_int(row.get('Payment Type Usage')),
                queue_type=parse_str(row.get('Queue Type')),
                total_due=parse_float(row.get('Total Due')),
                cash_back=parse_float(row.get('Cash Back')),
                change_due=parse_float(row.get('Change Due')),
                transaction_fee=parse_float(row.get('Transaction Fee')),
                payment_received=parse_float(row.get('Payment Received')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(PaymentsSnapshot.id)))

    return {
        "table": "payments_snapshot",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped,
        "total_in_db": final_count
    }


# ============================================================================
# INGEST ALL FUNCTION
# ============================================================================

async def ingest_all_reports(db: AsyncSession, base_path: str = None) -> dict:
    """
    Ingest ALL Blaze report CSVs.

    This function provides PERFECT DATA PARITY by ingesting all available reports.
    Entities are ingested first (vendors, products, consumers) since other reports
    may reference them.
    """
    # Import all extended ingestion modules
    from app.services.entities_ingestion import (
        ingest_vendors, ingest_product_catalog, ingest_product_batches, ingest_consumers
    )
    from app.services.employees_ingestion import (
        ingest_employee_performance, ingest_employee_activity, ingest_time_clock
    )
    from app.services.members_ingestion import (
        ingest_member_performance, ingest_inactive_members, ingest_marketing
    )
    from app.services.extended_sales_ingestion import (
        ingest_delivery_sales, ingest_canceled_void_sales, ingest_uncomplete_sales,
        ingest_promotions_activity, ingest_profit_loss, ingest_purchase_order_by_category,
        ingest_return_to_vendor, ingest_refund_history_detail, ingest_paidinout_activity
    )
    from app.services.inventory_extended_ingestion import (
        ingest_inventory_aging, ingest_inventory_distribution, ingest_inventory_valuation,
        ingest_inventory_transfers, ingest_sell_through, ingest_current_inventory
    )
    from app.services.sales_breakdowns_ingestion import (
        ingest_sales_by_city, ingest_sales_by_consumer_type, ingest_sales_by_hour,
        ingest_sales_by_product, ingest_sales_by_product_category, ingest_sales_by_vendor,
        ingest_employee_sales_by_product, ingest_products_by_vendor,
        ingest_product_sales_by_inventory, ingest_product_sell_by_expire
    )

    results = {}
    errors = []

    # Define all ingestion functions in dependency order
    ingestion_functions = [
        # Phase 1: Entity master data (must come first)
        ("vendors", ingest_vendors),
        ("product_catalog", ingest_product_catalog),
        ("product_batches", ingest_product_batches),
        ("consumers", ingest_consumers),
        # Phase 2: Original report types
        ("refund_history", ingest_refund_history),
        ("sales_payments", ingest_sales_payments),
        ("sales_by_queue", ingest_sales_by_queue),
        ("received_inventory", ingest_received_inventory),
        ("inventory_snapshot", ingest_inventory_snapshot),
        ("inventory_reconciliation", ingest_inventory_reconciliation),
        ("inventory_actions", ingest_inventory_actions),
        ("daily_accounting", ingest_daily_accounting),
        ("cash_drawer", ingest_cash_drawer),
        ("discount_usage", ingest_discount_usage),
        ("integrated_payments", ingest_integrated_payments),
        ("payments_snapshot", ingest_payments_snapshot),
        # Phase 3: Employee reports
        ("employee_performance", ingest_employee_performance),
        ("employee_activity", ingest_employee_activity),
        ("time_clock", ingest_time_clock),
        # Phase 4: Member reports
        ("member_performance", ingest_member_performance),
        ("inactive_members", ingest_inactive_members),
        ("marketing", ingest_marketing),
        # Phase 5: Extended sales
        ("delivery_sales", ingest_delivery_sales),
        ("canceled_void_sales", ingest_canceled_void_sales),
        ("uncomplete_sales", ingest_uncomplete_sales),
        ("promotions_activity", ingest_promotions_activity),
        ("profit_loss", ingest_profit_loss),
        ("purchase_order_by_category", ingest_purchase_order_by_category),
        ("return_to_vendor", ingest_return_to_vendor),
        ("refund_history_detail", ingest_refund_history_detail),
        ("paidinout_activity", ingest_paidinout_activity),
        # Phase 6: Inventory extended
        ("inventory_aging", ingest_inventory_aging),
        ("inventory_distribution", ingest_inventory_distribution),
        ("inventory_valuation", ingest_inventory_valuation),
        ("inventory_transfers", ingest_inventory_transfers),
        ("sell_through", ingest_sell_through),
        ("current_inventory", ingest_current_inventory),
        # Phase 7: Sales breakdowns
        ("sales_by_city", ingest_sales_by_city),
        ("sales_by_consumer_type", ingest_sales_by_consumer_type),
        ("sales_by_hour", ingest_sales_by_hour),
        ("sales_by_product", ingest_sales_by_product),
        ("sales_by_product_category", ingest_sales_by_product_category),
        ("sales_by_vendor", ingest_sales_by_vendor),
        ("employee_sales_by_product", ingest_employee_sales_by_product),
        ("products_by_vendor", ingest_products_by_vendor),
        ("product_sales_by_inventory", ingest_product_sales_by_inventory),
        ("product_sell_by_expire", ingest_product_sell_by_expire),
    ]

    for report_type, ingest_func in ingestion_functions:
        try:
            result = await ingest_func(db)
            results[report_type] = {"status": "success", **result}
        except Exception as e:
            logger.error(f"Error ingesting {report_type}: {e}")
            results[report_type] = {"status": "error", "error": str(e)}
            errors.append(report_type)
            # Rollback so the session can be reused for subsequent ingestions
            await db.rollback()

    return {
        "status": "complete" if not errors else "partial",
        "files_processed": len([r for r in results.values() if r.get("status") == "success"]),
        "files_skipped": len([r for r in results.values() if r.get("status") == "skipped"]),
        "files_errored": len(errors),
        "results": results,
        "errors": errors
    }
