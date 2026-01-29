#!/usr/bin/env python3
"""
Comprehensive Blaze Data Ingestion Script

This script ingests ALL Blaze CSV reports into the database with PERFECT DATA PARITY.
It can be run standalone without the API server.

Usage:
    python ingest_all.py [--base-path /opt/docker/blazedb] [--db-url sqlite:///blazedb.sqlite]
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime

# Add the services/api/app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

# Import models to ensure they're registered
from app.models.transaction import (
    Transaction, Member, Employee, Product, ProductSale, InventorySnapshot, DiscountUsage
)
from app.models.reports import (
    RefundHistory, SalesPayment, SalesByQueue, ReceivedInventory,
    InventoryReconciliation, InventoryAction, DailyAccountingSummary,
    CashDrawer, IntegratedPayment, PaymentsSnapshot
)
from app.core.database import Base

# Import ingestion functions
from app.services.ingestion import ingest_csv
from app.services.sales_details_ingestion import ingest_sales_details_csv
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
)


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(name: str, result: dict):
    """Print ingestion result."""
    status = result.get("status", "unknown")
    inserted = result.get("inserted", 0)
    skipped = result.get("skipped_duplicate", 0)
    total = result.get("csv_rows", result.get("total_in_db", 0))

    status_icon = "" if status == "success" else "" if status == "skipped" else ""
    print(f"  {status_icon} {name}")
    if status == "success":
        print(f"     Inserted: {inserted:,} | Skipped: {skipped:,} | Total in DB: {result.get('total_in_db', 'N/A')}")
    elif status == "skipped":
        print(f"     Reason: {result.get('reason', 'unknown')}")
    elif status == "error":
        print(f"     Error: {result.get('error', 'unknown')}")


async def create_tables(engine):
    """Create all tables using SQLAlchemy models."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  Tables created/verified")


async def run_migrations(engine, migrations_path: str):
    """Run SQL migrations."""
    migration_files = sorted([
        f for f in os.listdir(migrations_path)
        if f.endswith('.sql')
    ])

    for migration_file in migration_files:
        migration_path = os.path.join(migrations_path, migration_file)
        print(f"  Running migration: {migration_file}")

        async with engine.begin() as conn:
            with open(migration_path, 'r') as f:
                sql = f.read()
                # Split by semicolons and execute each statement
                for statement in sql.split(';'):
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            await conn.execute(text(statement))
                        except Exception as e:
                            # Ignore errors for IF NOT EXISTS statements
                            if "already exists" not in str(e).lower():
                                print(f"     Warning: {e}")


async def ingest_all(base_path: str, db_url: str):
    """Run all ingestions."""
    print_header("BLAZE DATA INGESTION - PERFECT DATA PARITY")
    print(f"  Base Path: {base_path}")
    print(f"  Database: {db_url}")
    print(f"  Started: {datetime.now().isoformat()}")

    # Create engine and session
    engine = create_async_engine(
        db_url,
        echo=False,
    )

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables
    print_header("CREATING TABLES")
    await create_tables(engine)

    # Run migrations
    migrations_path = os.path.join(base_path, 'migrations')
    if os.path.exists(migrations_path):
        print_header("RUNNING MIGRATIONS")
        await run_migrations(engine, migrations_path)

    results = {}

    # Define all CSV files and their ingestion functions
    csv_files = [
        ("total_sales.csv", ingest_csv, "Transactions"),
        ("COMPLETED_SALES_DETAILS_REPORT.csv", ingest_sales_details_csv, "Product Sales Details"),
        ("refund_history_report.csv", ingest_refund_history, "Refund History"),
        ("sales_payments_report.csv", ingest_sales_payments, "Sales Payments"),
        ("sales_by_queue_insights.csv", ingest_sales_by_queue, "Sales by Queue"),
        ("received_inventory.csv", ingest_received_inventory, "Received Inventory"),
        ("inventory_snapshot_report_insights.csv", ingest_inventory_snapshot, "Inventory Snapshots"),
        ("inventory_reconciliation_history_insights.csv", ingest_inventory_reconciliation, "Inventory Reconciliation"),
        ("inventory_action_summary.csv", ingest_inventory_actions, "Inventory Actions"),
        ("daily_accounting_summary.csv", ingest_daily_accounting, "Daily Accounting"),
        ("cash_drawer_insights.csv", ingest_cash_drawer, "Cash Drawer"),
        ("unified_discount.csv", ingest_discount_usage, "Discount Usage"),
        ("integrated_payments_report.csv", ingest_integrated_payments, "Integrated Payments"),
        ("payments_snapshot.csv", ingest_payments_snapshot, "Payments Snapshot"),
    ]

    print_header("INGESTING CSV FILES")

    total_inserted = 0
    files_success = 0
    files_skipped = 0
    files_error = 0

    for filename, ingest_func, display_name in csv_files:
        csv_path = os.path.join(base_path, filename)

        if not os.path.exists(csv_path):
            results[filename] = {"status": "skipped", "reason": "file not found"}
            files_skipped += 1
            print_result(display_name, results[filename])
            continue

        try:
            async with async_session() as session:
                if filename == "total_sales.csv":
                    result = await ingest_func(session, csv_path, force_reimport=False)
                else:
                    result = await ingest_func(session, csv_path)

                result["status"] = "success"
                results[filename] = result
                total_inserted += result.get("inserted", 0)
                files_success += 1
                print_result(display_name, result)

        except Exception as e:
            results[filename] = {"status": "error", "error": str(e)}
            files_error += 1
            print_result(display_name, results[filename])

    # Print summary
    print_header("INGESTION SUMMARY")
    print(f"  Total Records Inserted: {total_inserted:,}")
    print(f"  Files Successful: {files_success}")
    print(f"  Files Skipped: {files_skipped}")
    print(f"  Files Errored: {files_error}")
    print(f"  Completed: {datetime.now().isoformat()}")

    # Print table counts
    print_header("DATABASE TABLE COUNTS")
    async with async_session() as session:
        from sqlalchemy import select, func

        tables = [
            ("transactions", Transaction),
            ("product_sales", ProductSale),
            ("products", Product),
            ("members", Member),
            ("employees", Employee),
            ("refund_history", RefundHistory),
            ("sales_payments", SalesPayment),
            ("sales_by_queue", SalesByQueue),
            ("received_inventory", ReceivedInventory),
            ("inventory_snapshots", InventorySnapshot),
            ("inventory_reconciliation", InventoryReconciliation),
            ("inventory_actions", InventoryAction),
            ("daily_accounting_summary", DailyAccountingSummary),
            ("cash_drawers", CashDrawer),
            ("discount_usage", DiscountUsage),
            ("integrated_payments", IntegratedPayment),
            ("payments_snapshot", PaymentsSnapshot),
        ]

        total_count = 0
        for name, model in tables:
            try:
                count = await session.scalar(select(func.count(model.id)))
                total_count += count
                print(f"  {name}: {count:,}")
            except Exception as e:
                print(f"  {name}: Error - {e}")

        print(f"\n  TOTAL RECORDS: {total_count:,}")

    await engine.dispose()

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Ingest all Blaze CSV reports into the database"
    )
    parser.add_argument(
        "--base-path",
        default="/opt/docker/blazedb",
        help="Base path containing CSV files (default: /opt/docker/blazedb)"
    )
    parser.add_argument(
        "--db-url",
        default="sqlite+aiosqlite:///blazedb.sqlite",
        help="Database URL (default: sqlite+aiosqlite:///blazedb.sqlite)"
    )

    args = parser.parse_args()

    asyncio.run(ingest_all(args.base_path, args.db_url))


if __name__ == "__main__":
    main()
