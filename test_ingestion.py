#!/usr/bin/env python3
"""
Quick test script to verify imports and basic functionality.
"""

import os
import sys

# Add the services/api/app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from app.models.transaction import (
            Transaction, Member, Employee, Product, ProductSale,
            InventorySnapshot, DiscountUsage
        )
        print("  [OK] Core models imported")
    except Exception as e:
        print(f"  [FAIL] Core models: {e}")
        return False

    try:
        from app.models.reports import (
            RefundHistory, SalesPayment, SalesByQueue, ReceivedInventory,
            InventoryReconciliation, InventoryAction, DailyAccountingSummary,
            CashDrawer, IntegratedPayment, PaymentsSnapshot
        )
        print("  [OK] Report models imported")
    except Exception as e:
        print(f"  [FAIL] Report models: {e}")
        return False

    try:
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
        print("  [OK] Reports ingestion imported")
    except Exception as e:
        print(f"  [FAIL] Reports ingestion: {e}")
        return False

    try:
        from app.services.ingestion import ingest_csv
        from app.services.sales_details_ingestion import ingest_sales_details_csv
        print("  [OK] Core ingestion imported")
    except Exception as e:
        print(f"  [FAIL] Core ingestion: {e}")
        return False

    return True


def test_csv_files():
    """Check that CSV files exist."""
    print("\nChecking CSV files...")

    base_path = "/opt/docker/blazedb"
    csv_files = [
        "total_sales.csv",
        "COMPLETED_SALES_DETAILS_REPORT.csv",
        "refund_history_report.csv",
        "sales_payments_report.csv",
        "sales_by_queue_insights.csv",
        "received_inventory.csv",
        "inventory_snapshot_report_insights.csv",
        "inventory_reconciliation_history_insights.csv",
        "inventory_action_summary.csv",
        "daily_accounting_summary.csv",
        "cash_drawer_insights.csv",
        "unified_discount.csv",
        "integrated_payments_report.csv",
        "payments_snapshot.csv",
    ]

    found = 0
    for csv_file in csv_files:
        path = os.path.join(base_path, csv_file)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  [OK] {csv_file} ({size:,} bytes)")
            found += 1
        else:
            print(f"  [--] {csv_file} (not found)")

    print(f"\n  Found {found}/{len(csv_files)} CSV files")
    return found > 0


def main():
    print("=" * 60)
    print("  BLAZEDB INGESTION TEST")
    print("=" * 60)

    imports_ok = test_imports()
    files_ok = test_csv_files()

    print("\n" + "=" * 60)
    if imports_ok and files_ok:
        print("  All tests passed!")
        print("\n  To run full ingestion:")
        print("    cd /opt/docker/blazedb")
        print("    python ingest_all.py")
        print("\n  Or via API (if running):")
        print("    curl -X POST http://localhost:8001/api/v1/ingest/all")
    else:
        print("  Some tests failed!")
        return 1

    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
