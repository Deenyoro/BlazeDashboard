from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
import os
import tempfile
from datetime import datetime

from app.core.database import get_db
from app.services.ingestion import ingest_csv, validate_no_duplicates, get_last_transaction_date
from app.services.sales_details_ingestion import ingest_sales_details_csv, get_sales_details_stats
from app.services.reports_ingestion import (
    ingest_refund_history,
    ingest_sales_payments,
    ingest_sales_by_queue,
    ingest_received_inventory,
    ingest_inventory_snapshot,
    ingest_inventory_reconciliation,
    ingest_inventory_actions,
    ingest_daily_accounting,
    ingest_cash_drawer,
    ingest_discount_usage,
    ingest_integrated_payments,
    ingest_payments_snapshot,
    ingest_all_reports,
)
from app.services.employees_ingestion import (
    ingest_employee_performance,
    ingest_employee_activity,
    ingest_time_clock,
)
from app.services.members_ingestion import (
    ingest_member_performance,
    ingest_inactive_members,
    ingest_marketing,
)
from app.services.extended_sales_ingestion import (
    ingest_delivery_sales,
    ingest_canceled_void_sales,
    ingest_uncomplete_sales,
    ingest_promotions_activity,
    ingest_profit_loss,
    ingest_purchase_order_by_category,
    ingest_return_to_vendor,
    ingest_refund_history_detail,
    ingest_paidinout_activity,
)
from app.services.inventory_extended_ingestion import (
    ingest_inventory_aging,
    ingest_inventory_distribution,
    ingest_inventory_valuation,
    ingest_inventory_transfers,
    ingest_sell_through,
    ingest_current_inventory,
)
from app.services.sales_breakdowns_ingestion import (
    ingest_sales_by_city,
    ingest_sales_by_hour,
    ingest_sales_by_product,
    ingest_sales_by_product_category,
    ingest_sales_by_vendor,
    ingest_sales_by_consumer_type,
    ingest_employee_sales_by_product,
    ingest_products_by_vendor,
    ingest_product_sales_by_inventory,
    ingest_product_sell_by_expire,
)
from app.models.transaction import Transaction, Member, Employee, ProductSale, Product, InventorySnapshot, DiscountUsage
from app.models.reports import (
    RefundHistory, SalesPayment, SalesByQueue, ReceivedInventory,
    InventoryReconciliation, InventoryAction, DailyAccountingSummary,
    CashDrawer, IntegratedPayment, PaymentsSnapshot
)
from app.models.entities import Vendor, ProductCatalog, ProductBatch, Consumer
from app.models.employees_extended import EmployeePerformance, EmployeeActivity, TimeClock
from app.models.members_extended import MemberPerformance, InactiveMember, MarketingContact
from app.models.sales_extended import (
    DeliverySale, CanceledVoidSale, UncompleteSale, PromotionsActivity,
    ProfitLoss, PurchaseOrderByCategory, ReturnToVendor, RefundHistoryDetail,
    PaidInOutActivity, InventoryAging, InventoryDistribution, InventoryValuation,
    InventoryTransfer, SellThrough, CurrentInventory, SalesByCity, SalesByHour,
    SalesByProduct, SalesByProductCategory, SalesByVendor, SalesByConsumerType,
    EmployeeSalesByProduct, ProductsByVendor, ProductSalesByInventory, ProductSellByExpire,
)

router = APIRouter()


# ============================================================================
# CORE INGESTION ENDPOINTS (Transaction & Product Sales)
# ============================================================================

@router.post("/csv")
async def ingest_csv_file(
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(None),
    use_default: bool = Query(True),
    force_reimport: bool = Query(False, description="Force re-import (updates existing records)"),
):
    """
    Ingest transactions from CSV file.

    DEDUPLICATION: Uses Trans ID (blaze_trans_id) as unique identifier.
    - Existing transactions are SKIPPED (not duplicated)
    - Returns detailed counts of inserted vs skipped records

    If use_default=True, uses the default /app/data/total_sales.csv file.
    Otherwise, uploads and processes the provided file.
    """
    if use_default:
        csv_path = "/app/data/total_sales.csv"
        if not os.path.exists(csv_path):
            return {"error": "Default CSV file not found", "path": csv_path}
    else:
        if not file:
            return {"error": "No file provided"}

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            content = await file.read()
            tmp.write(content)
            csv_path = tmp.name

    try:
        result = await ingest_csv(db, csv_path, force_reimport=force_reimport)

        # Add duplicate validation check
        duplicate_check = await validate_no_duplicates(db)
        result["duplicate_validation"] = duplicate_check

        return {"status": "success", **result}
    finally:
        # Clean up temp file if we created one
        if not use_default and csv_path:
            try:
                os.unlink(csv_path)
            except Exception:
                pass


@router.get("/status")
async def ingestion_status(db: AsyncSession = Depends(get_db)):
    """Get current database status and counts."""
    trans_count = await db.scalar(select(func.count(Transaction.id)))
    member_count = await db.scalar(select(func.count(Member.id)))
    employee_count = await db.scalar(select(func.count(Employee.id)))

    # Date range
    date_range = await db.execute(
        select(
            func.min(Transaction.date).label("min_date"),
            func.max(Transaction.date).label("max_date"),
        )
    )
    dates = date_range.one()

    # Transaction types breakdown
    type_counts = await db.execute(
        select(
            Transaction.trans_type,
            func.count(Transaction.id).label("count"),
        ).group_by(Transaction.trans_type)
    )

    by_type = {row.trans_type: row.count for row in type_counts.all()}

    return {
        "transactions": trans_count,
        "members": member_count,
        "employees": employee_count,
        "date_range": {
            "start": dates.min_date.isoformat() if dates.min_date else None,
            "end": dates.max_date.isoformat() if dates.max_date else None,
        },
        "by_type": by_type,
    }


@router.get("/validate")
async def validate_data(db: AsyncSession = Depends(get_db)):
    """
    Validate database integrity - check for duplicate transactions.
    This endpoint ensures no Trans IDs are duplicated.
    """
    duplicate_check = await validate_no_duplicates(db)

    # Get total counts
    trans_count = await db.scalar(select(func.count(Transaction.id)))

    # Count unique Trans IDs
    unique_count = await db.scalar(
        select(func.count(func.distinct(Transaction.blaze_trans_id)))
    )

    return {
        "total_transactions": trans_count,
        "unique_trans_ids": unique_count,
        "duplicates": duplicate_check,
        "data_integrity": "PASS" if not duplicate_check["has_duplicates"] else "FAIL",
        "validated_at": datetime.utcnow().isoformat(),
    }


@router.get("/last-date")
async def get_last_date(db: AsyncSession = Depends(get_db)):
    """Get the date of the most recent transaction in the database."""
    last_date = await get_last_transaction_date(db)
    return {
        "last_transaction_date": last_date.isoformat() if last_date else None,
        "last_transaction_date_formatted": last_date.strftime("%Y-%m-%d") if last_date else None,
    }


@router.post("/sales-details")
async def ingest_sales_details(
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(None),
    use_default: bool = Query(True),
    csv_path: str = Query(None, description="Path to CSV file on server"),
):
    """
    Ingest product-level sales data from Completed Sales Details Report CSV.

    This CSV format has one row per product sold with detailed financial info.

    DEDUPLICATION: Uses hash of trans_no + date + sku + product_name + batch + metrc_tag + net_sales + quantity.
    - Existing product sales are SKIPPED (not duplicated)
    - Returns detailed counts of inserted vs skipped records

    Options:
    - use_default=True: Uses /app/data/completed_sales_details_report.csv
    - csv_path: Specify a custom path to the CSV file on the server
    - file: Upload a CSV file directly
    """
    if csv_path:
        # Use specified path
        if not os.path.exists(csv_path):
            return {"error": "CSV file not found", "path": csv_path}
        final_path = csv_path
    elif use_default:
        # Try common locations
        default_paths = [
            "/app/data/completed_sales_details_report.csv",
        ]
        final_path = None
        for path in default_paths:
            if os.path.exists(path):
                final_path = path
                break
        if not final_path:
            return {"error": "Default CSV file not found", "tried_paths": default_paths}
    else:
        if not file:
            return {"error": "No file provided"}

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            content = await file.read()
            tmp.write(content)
            final_path = tmp.name

    try:
        result = await ingest_sales_details_csv(db, final_path)
        return {"status": "success", "csv_path": final_path, **result}
    finally:
        # Clean up temp file if we created one
        if not use_default and not csv_path and final_path:
            try:
                os.unlink(final_path)
            except Exception:
                pass


@router.get("/sales-details/status")
async def sales_details_status(db: AsyncSession = Depends(get_db)):
    """Get current product sales database status and counts."""
    stats = await get_sales_details_stats(db)

    # Also get product and member counts
    product_count = await db.scalar(select(func.count(Product.id)))
    member_count = await db.scalar(select(func.count(Member.id)))
    employee_count = await db.scalar(select(func.count(Employee.id)))

    return {
        **stats,
        "products": product_count,
        "members": member_count,
        "employees": employee_count,
    }


# ============================================================================
# COMPREHENSIVE INGESTION - ALL REPORTS
# ============================================================================

@router.post("/all")
async def ingest_all_csv_files(
    db: AsyncSession = Depends(get_db),
    base_path: str = Query("/app/data", description="Base path for CSV files"),
    include_transactions: bool = Query(True, description="Include total_sales.csv"),
    include_sales_details: bool = Query(True, description="Include completed_sales_details_report.csv"),
):
    """
    INGEST ALL BLAZE CSV REPORTS - PERFECT DATA PARITY

    This endpoint ingests ALL available Blaze report CSVs:
    - total_sales.csv (transactions)
    - completed_sales_details_report.csv (product-level sales)
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

    All data is deduplicated - running multiple times is safe.
    """
    results = {}

    # 1. Ingest transactions (total_sales.csv)
    if include_transactions:
        trans_path = os.path.join(base_path, "total_sales.csv")
        if os.path.exists(trans_path):
            try:
                result = await ingest_csv(db, trans_path, force_reimport=False)
                results["total_sales.csv"] = {"status": "success", **result}
            except Exception as e:
                results["total_sales.csv"] = {"status": "error", "error": str(e)}
        else:
            results["total_sales.csv"] = {"status": "skipped", "reason": "file not found"}

    # 2. Ingest sales details (completed_sales_details_report.csv)
    if include_sales_details:
        details_path = os.path.join(base_path, "completed_sales_details_report.csv")
        if os.path.exists(details_path):
            try:
                result = await ingest_sales_details_csv(db, details_path)
                results["completed_sales_details_report.csv"] = {"status": "success", **result}
            except Exception as e:
                results["completed_sales_details_report.csv"] = {"status": "error", "error": str(e)}
        else:
            results["completed_sales_details_report.csv"] = {"status": "skipped", "reason": "file not found"}

    # 3. Ingest all other reports
    other_results = await ingest_all_reports(db, base_path)
    results.update(other_results.get("results", {}))

    # Calculate totals
    total_inserted = sum(
        r.get("inserted", 0) for r in results.values() if isinstance(r, dict)
    )
    files_success = len([r for r in results.values() if isinstance(r, dict) and r.get("status") == "success"])
    files_skipped = len([r for r in results.values() if isinstance(r, dict) and r.get("status") == "skipped"])
    files_error = len([r for r in results.values() if isinstance(r, dict) and r.get("status") == "error"])

    return {
        "status": "complete",
        "summary": {
            "total_records_inserted": total_inserted,
            "files_success": files_success,
            "files_skipped": files_skipped,
            "files_error": files_error,
        },
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/all/status")
async def all_tables_status(db: AsyncSession = Depends(get_db)):
    """Get counts for ALL tables in the database."""
    counts = {}

    # Core tables
    counts["transactions"] = await db.scalar(select(func.count(Transaction.id)))
    counts["product_sales"] = await db.scalar(select(func.count(ProductSale.id)))
    counts["products"] = await db.scalar(select(func.count(Product.id)))
    counts["members"] = await db.scalar(select(func.count(Member.id)))
    counts["employees"] = await db.scalar(select(func.count(Employee.id)))

    # Report tables
    counts["refund_history"] = await db.scalar(select(func.count(RefundHistory.id)))
    counts["sales_payments"] = await db.scalar(select(func.count(SalesPayment.id)))
    counts["sales_by_queue"] = await db.scalar(select(func.count(SalesByQueue.id)))
    counts["received_inventory"] = await db.scalar(select(func.count(ReceivedInventory.id)))
    counts["inventory_snapshots"] = await db.scalar(select(func.count(InventorySnapshot.id)))
    counts["inventory_reconciliation"] = await db.scalar(select(func.count(InventoryReconciliation.id)))
    counts["inventory_actions"] = await db.scalar(select(func.count(InventoryAction.id)))
    counts["daily_accounting_summary"] = await db.scalar(select(func.count(DailyAccountingSummary.id)))
    counts["cash_drawers"] = await db.scalar(select(func.count(CashDrawer.id)))
    counts["discount_usage"] = await db.scalar(select(func.count(DiscountUsage.id)))
    counts["integrated_payments"] = await db.scalar(select(func.count(IntegratedPayment.id)))
    counts["payments_snapshot"] = await db.scalar(select(func.count(PaymentsSnapshot.id)))

    # Entity tables
    counts["vendors"] = await db.scalar(select(func.count(Vendor.id)))
    counts["product_catalog"] = await db.scalar(select(func.count(ProductCatalog.id)))
    counts["product_batches"] = await db.scalar(select(func.count(ProductBatch.id)))
    counts["consumers"] = await db.scalar(select(func.count(Consumer.id)))

    # Employee extended tables
    counts["employee_performance"] = await db.scalar(select(func.count(EmployeePerformance.id)))
    counts["employee_activity"] = await db.scalar(select(func.count(EmployeeActivity.id)))
    counts["time_clock"] = await db.scalar(select(func.count(TimeClock.id)))

    # Member tables
    counts["member_performance"] = await db.scalar(select(func.count(MemberPerformance.id)))
    counts["inactive_members"] = await db.scalar(select(func.count(InactiveMember.id)))
    counts["marketing_contacts"] = await db.scalar(select(func.count(MarketingContact.id)))

    # Extended sales tables
    counts["delivery_sales"] = await db.scalar(select(func.count(DeliverySale.id)))
    counts["canceled_void_sales"] = await db.scalar(select(func.count(CanceledVoidSale.id)))
    counts["uncomplete_sales"] = await db.scalar(select(func.count(UncompleteSale.id)))
    counts["promotions_activity"] = await db.scalar(select(func.count(PromotionsActivity.id)))
    counts["profit_loss"] = await db.scalar(select(func.count(ProfitLoss.id)))
    counts["purchase_order_by_category"] = await db.scalar(select(func.count(PurchaseOrderByCategory.id)))
    counts["return_to_vendor"] = await db.scalar(select(func.count(ReturnToVendor.id)))
    counts["refund_history_detail"] = await db.scalar(select(func.count(RefundHistoryDetail.id)))
    counts["paidinout_activity"] = await db.scalar(select(func.count(PaidInOutActivity.id)))

    # Extended inventory tables
    counts["inventory_aging"] = await db.scalar(select(func.count(InventoryAging.id)))
    counts["inventory_distribution"] = await db.scalar(select(func.count(InventoryDistribution.id)))
    counts["inventory_valuation"] = await db.scalar(select(func.count(InventoryValuation.id)))
    counts["inventory_transfers"] = await db.scalar(select(func.count(InventoryTransfer.id)))
    counts["sell_through"] = await db.scalar(select(func.count(SellThrough.id)))
    counts["current_inventory"] = await db.scalar(select(func.count(CurrentInventory.id)))

    # Sales breakdown tables
    counts["sales_by_city"] = await db.scalar(select(func.count(SalesByCity.id)))
    counts["sales_by_hour"] = await db.scalar(select(func.count(SalesByHour.id)))
    counts["sales_by_product"] = await db.scalar(select(func.count(SalesByProduct.id)))
    counts["sales_by_product_category"] = await db.scalar(select(func.count(SalesByProductCategory.id)))
    counts["sales_by_vendor"] = await db.scalar(select(func.count(SalesByVendor.id)))
    counts["sales_by_consumer_type"] = await db.scalar(select(func.count(SalesByConsumerType.id)))
    counts["employee_sales_by_product"] = await db.scalar(select(func.count(EmployeeSalesByProduct.id)))
    counts["products_by_vendor"] = await db.scalar(select(func.count(ProductsByVendor.id)))
    counts["product_sales_by_inventory"] = await db.scalar(select(func.count(ProductSalesByInventory.id)))
    counts["product_sell_by_expire"] = await db.scalar(select(func.count(ProductSellByExpire.id)))

    total_records = sum(counts.values())

    return {
        "total_records": total_records,
        "tables": counts,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# INDIVIDUAL REPORT INGESTION ENDPOINTS
# ============================================================================

@router.post("/refund-history")
async def ingest_refund_history_endpoint(
    db: AsyncSession = Depends(get_db),
    csv_path: str = Query(None),
):
    """Ingest refund_history_report.csv."""
    final_path = find_csv("refund_history_report.csv", csv_path, subdir="sales")
    if not final_path:
        return {"error": "CSV file not found"}
    result = await ingest_refund_history(db, final_path)
    return {"status": "success", **result}


def find_csv(filename: str, custom_path: str = None, subdir: str = None) -> str:
    """Find CSV file from multiple possible locations."""
    paths = [custom_path] if custom_path else []
    if subdir:
        paths.extend([
            f"/app/data/{subdir}/{filename}",
        ])
    paths.extend([
        f"/app/data/{filename}",
        f"/opt/docker/blazedb/{filename}",
    ])
    return next((p for p in paths if p and os.path.exists(p)), None)


@router.post("/sales-payments")
async def ingest_sales_payments_endpoint(
    db: AsyncSession = Depends(get_db),
    csv_path: str = Query(None),
):
    """Ingest sales_payments_report.csv."""
    final_path = find_csv("sales_payments_report.csv", csv_path, subdir="payments")
    if not final_path:
        return {"error": "CSV file not found"}
    result = await ingest_sales_payments(db, final_path)
    return {"status": "success", **result}


@router.post("/sales-by-queue")
async def ingest_sales_by_queue_endpoint(
    db: AsyncSession = Depends(get_db),
    csv_path: str = Query(None),
):
    """Ingest sales_by_queue_insights.csv."""
    final_path = find_csv("sales_by_queue_insights.csv", csv_path, subdir="sales")
    if not final_path:
        return {"error": "CSV file not found"}
    result = await ingest_sales_by_queue(db, final_path)
    return {"status": "success", **result}


@router.post("/received-inventory")
async def ingest_received_inventory_endpoint(
    db: AsyncSession = Depends(get_db),
    csv_path: str = Query(None),
):
    """Ingest received_inventory.csv."""
    final_path = find_csv("received_inventory.csv", csv_path, subdir="inventory")
    if not final_path:
        return {"error": "CSV file not found"}
    result = await ingest_received_inventory(db, final_path)
    return {"status": "success", **result}


@router.post("/inventory-snapshot")
async def ingest_inventory_snapshot_endpoint(
    db: AsyncSession = Depends(get_db),
    csv_path: str = Query(None),
):
    """Ingest inventory_snapshot_report_insights.csv."""
    final_path = find_csv("inventory_snapshot_report_insights.csv", csv_path, subdir="inventory")
    if not final_path:
        return {"error": "CSV file not found"}
    result = await ingest_inventory_snapshot(db, final_path)
    return {"status": "success", **result}


@router.post("/inventory-reconciliation")
async def ingest_inventory_reconciliation_endpoint(
    db: AsyncSession = Depends(get_db),
    csv_path: str = Query(None),
):
    """Ingest inventory_reconciliation_history_insights.csv."""
    final_path = find_csv("inventory_reconciliation_history_insights.csv", csv_path, subdir="inventory")
    if not final_path:
        return {"error": "CSV file not found"}
    result = await ingest_inventory_reconciliation(db, final_path)
    return {"status": "success", **result}


@router.post("/inventory-actions")
async def ingest_inventory_actions_endpoint(
    db: AsyncSession = Depends(get_db),
    csv_path: str = Query(None),
):
    """Ingest inventory_action_summary.csv."""
    final_path = find_csv("inventory_action_summary.csv", csv_path, subdir="inventory")
    if not final_path:
        return {"error": "CSV file not found"}
    result = await ingest_inventory_actions(db, final_path)
    return {"status": "success", **result}


@router.post("/daily-accounting")
async def ingest_daily_accounting_endpoint(
    db: AsyncSession = Depends(get_db),
    csv_path: str = Query(None),
):
    """Ingest daily_accounting_summary.csv."""
    final_path = find_csv("daily_accounting_summary.csv", csv_path, subdir="accounting")
    if not final_path:
        return {"error": "CSV file not found"}
    result = await ingest_daily_accounting(db, final_path)
    return {"status": "success", **result}


@router.post("/cash-drawer")
async def ingest_cash_drawer_endpoint(
    db: AsyncSession = Depends(get_db),
    csv_path: str = Query(None),
):
    """Ingest cash_drawer_insights.csv."""
    final_path = find_csv("cash_drawer_insights.csv", csv_path, subdir="accounting")
    if not final_path:
        return {"error": "CSV file not found"}
    result = await ingest_cash_drawer(db, final_path)
    return {"status": "success", **result}


@router.post("/discount-usage")
async def ingest_discount_usage_endpoint(
    db: AsyncSession = Depends(get_db),
    csv_path: str = Query(None),
):
    """Ingest unified_discount.csv."""
    final_path = find_csv("unified_discount.csv", csv_path, subdir="promotions")
    if not final_path:
        return {"error": "CSV file not found"}
    result = await ingest_discount_usage(db, final_path)
    return {"status": "success", **result}


@router.post("/integrated-payments")
async def ingest_integrated_payments_endpoint(
    db: AsyncSession = Depends(get_db),
    csv_path: str = Query(None),
):
    """Ingest integrated_payments_report.csv."""
    final_path = find_csv("integrated_payments_report.csv", csv_path, subdir="payments")
    if not final_path:
        return {"error": "CSV file not found"}
    result = await ingest_integrated_payments(db, final_path)
    return {"status": "success", **result}


@router.post("/payments-snapshot")
async def ingest_payments_snapshot_endpoint(
    db: AsyncSession = Depends(get_db),
    csv_path: str = Query(None),
):
    """Ingest payments_snapshot.csv."""
    final_path = find_csv("payments_snapshot.csv", csv_path, subdir="payments")
    if not final_path:
        return {"error": "CSV file not found"}
    result = await ingest_payments_snapshot(db, final_path)
    return {"status": "success", **result}


# ============================================================================
# EXTENDED DATA INGESTION - ALL REMAINING CSV FILES
# ============================================================================

@router.post("/extended")
async def ingest_extended_data(
    db: AsyncSession = Depends(get_db),
):
    """
    INGEST ALL EXTENDED DATA FROM REMAINING CSV FILES

    This ingests all additional reports beyond the core 14:
    - Employee data (performance, activity, time clock)
    - Member analytics (performance, inactive, marketing)
    - Extended sales (delivery, canceled, uncomplete, promotions, etc.)
    - Inventory extended (aging, distribution, valuation, transfers, etc.)
    - Sales breakdowns (by city, hour, product, category, vendor, etc.)

    All data is deduplicated - running multiple times is safe.
    """
    results = {}

    # Employee data
    extended_ingestions = [
        ("employee_performance", ingest_employee_performance),
        ("employee_activity", ingest_employee_activity),
        ("time_clock", ingest_time_clock),
        ("member_performance", ingest_member_performance),
        ("inactive_members", ingest_inactive_members),
        ("marketing_contacts", ingest_marketing),
        ("delivery_sales", ingest_delivery_sales),
        ("canceled_void_sales", ingest_canceled_void_sales),
        ("uncomplete_sales", ingest_uncomplete_sales),
        ("promotions_activity", ingest_promotions_activity),
        ("profit_loss", ingest_profit_loss),
        ("purchase_order_by_category", ingest_purchase_order_by_category),
        ("return_to_vendor", ingest_return_to_vendor),
        ("refund_history_detail", ingest_refund_history_detail),
        ("paidinout_activity", ingest_paidinout_activity),
        ("inventory_aging", ingest_inventory_aging),
        ("inventory_distribution", ingest_inventory_distribution),
        ("inventory_valuation", ingest_inventory_valuation),
        ("inventory_transfers", ingest_inventory_transfers),
        ("sell_through", ingest_sell_through),
        ("current_inventory", ingest_current_inventory),
        ("sales_by_city", ingest_sales_by_city),
        ("sales_by_hour", ingest_sales_by_hour),
        ("sales_by_product", ingest_sales_by_product),
        ("sales_by_product_category", ingest_sales_by_product_category),
        ("sales_by_vendor", ingest_sales_by_vendor),
        ("sales_by_consumer_type", ingest_sales_by_consumer_type),
        ("employee_sales_by_product", ingest_employee_sales_by_product),
        ("products_by_vendor", ingest_products_by_vendor),
        ("product_sales_by_inventory", ingest_product_sales_by_inventory),
        ("product_sell_by_expire", ingest_product_sell_by_expire),
    ]

    total_inserted = 0
    files_success = 0
    files_skipped = 0
    files_error = 0

    for name, ingest_func in extended_ingestions:
        try:
            result = await ingest_func(db)
            results[name] = result
            if result.get("status") == "skipped":
                files_skipped += 1
            else:
                result["status"] = "success"
                total_inserted += result.get("inserted", 0)
                files_success += 1
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
            files_error += 1

    return {
        "status": "complete",
        "summary": {
            "total_records_inserted": total_inserted,
            "files_success": files_success,
            "files_skipped": files_skipped,
            "files_error": files_error,
        },
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/complete")
async def ingest_complete(
    db: AsyncSession = Depends(get_db),
    base_path: str = Query("/app/data", description="Base path for CSV files"),
):
    """
    COMPLETE DATA INGESTION - ALL 59 CSV FILES

    This runs both /all (core 14 reports) and /extended (remaining 31 reports)
    to ingest every CSV file in the data folder.

    All data is deduplicated - running multiple times is safe.
    """
    # First run core ingestion
    core_results = {}

    # Ingest transactions
    trans_path = os.path.join(base_path, "total_sales.csv")
    if os.path.exists(trans_path):
        try:
            result = await ingest_csv(db, trans_path, force_reimport=False)
            core_results["total_sales.csv"] = {"status": "success", **result}
        except Exception as e:
            core_results["total_sales.csv"] = {"status": "error", "error": str(e)}

    # Ingest sales details
    details_path = os.path.join(base_path, "completed_sales_details_report.csv")
    if os.path.exists(details_path):
        try:
            result = await ingest_sales_details_csv(db, details_path)
            core_results["completed_sales_details_report.csv"] = {"status": "success", **result}
        except Exception as e:
            core_results["completed_sales_details_report.csv"] = {"status": "error", "error": str(e)}

    # Ingest all other core reports
    other_results = await ingest_all_reports(db, base_path)
    core_results.update(other_results.get("results", {}))

    # Now run extended ingestion
    extended_ingestions = [
        ("employee_performance", ingest_employee_performance),
        ("employee_activity", ingest_employee_activity),
        ("time_clock", ingest_time_clock),
        ("member_performance", ingest_member_performance),
        ("inactive_members", ingest_inactive_members),
        ("marketing_contacts", ingest_marketing),
        ("delivery_sales", ingest_delivery_sales),
        ("canceled_void_sales", ingest_canceled_void_sales),
        ("uncomplete_sales", ingest_uncomplete_sales),
        ("promotions_activity", ingest_promotions_activity),
        ("profit_loss", ingest_profit_loss),
        ("purchase_order_by_category", ingest_purchase_order_by_category),
        ("return_to_vendor", ingest_return_to_vendor),
        ("refund_history_detail", ingest_refund_history_detail),
        ("paidinout_activity", ingest_paidinout_activity),
        ("inventory_aging", ingest_inventory_aging),
        ("inventory_distribution", ingest_inventory_distribution),
        ("inventory_valuation", ingest_inventory_valuation),
        ("inventory_transfers", ingest_inventory_transfers),
        ("sell_through", ingest_sell_through),
        ("current_inventory", ingest_current_inventory),
        ("sales_by_city", ingest_sales_by_city),
        ("sales_by_hour", ingest_sales_by_hour),
        ("sales_by_product", ingest_sales_by_product),
        ("sales_by_product_category", ingest_sales_by_product_category),
        ("sales_by_vendor", ingest_sales_by_vendor),
        ("sales_by_consumer_type", ingest_sales_by_consumer_type),
        ("employee_sales_by_product", ingest_employee_sales_by_product),
        ("products_by_vendor", ingest_products_by_vendor),
        ("product_sales_by_inventory", ingest_product_sales_by_inventory),
        ("product_sell_by_expire", ingest_product_sell_by_expire),
    ]

    extended_results = {}
    for name, ingest_func in extended_ingestions:
        try:
            result = await ingest_func(db)
            extended_results[name] = result
            if result.get("status") != "skipped":
                result["status"] = "success"
        except Exception as e:
            extended_results[name] = {"status": "error", "error": str(e)}

    # Combine results
    all_results = {**core_results, **extended_results}

    # Calculate totals
    total_inserted = sum(
        r.get("inserted", 0) for r in all_results.values() if isinstance(r, dict)
    )
    files_success = len([r for r in all_results.values() if isinstance(r, dict) and r.get("status") == "success"])
    files_skipped = len([r for r in all_results.values() if isinstance(r, dict) and r.get("status") == "skipped"])
    files_error = len([r for r in all_results.values() if isinstance(r, dict) and r.get("status") == "error"])

    return {
        "status": "complete",
        "summary": {
            "total_records_inserted": total_inserted,
            "files_success": files_success,
            "files_skipped": files_skipped,
            "files_error": files_error,
        },
        "core_results": core_results,
        "extended_results": extended_results,
        "timestamp": datetime.utcnow().isoformat(),
    }
