"""Ingestion for extended employee data: performance, activity, time clock."""

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.models.employees_extended import EmployeePerformance, EmployeeActivity, TimeClock
from app.services.reports_ingestion import (
    parse_date, parse_datetime, parse_float, parse_int,
    parse_str, generate_hash, get_existing_hashes, DATA_DIR
)

logger = logging.getLogger(__name__)

CSV_PATHS_EMPLOYEES = {
    "employee_performance": f"{DATA_DIR}/master_employee_report.csv",
    "employee_activity": f"{DATA_DIR}/employee_activity.csv",
    "time_clock": f"{DATA_DIR}/time_clock_reports.csv",
}


async def ingest_employee_performance(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest master_employee_report.csv."""
    import os
    final_path = csv_path or CSV_PATHS_EMPLOYEES["employee_performance"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting employee performance from {final_path}")
    # This CSV has headers on row 0 (no title row)
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig')
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, EmployeePerformance, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            employee = parse_str(row.get('Sold By') or row.get('Employee'))
            if not date_val:
                continue

            line_hash = generate_hash(date_val, employee)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = EmployeePerformance(
                line_hash=line_hash,
                date=date_val,
                employee_name=employee,
                gross_receipts=parse_float(row.get('Gross Receipts')),
                transaction_count=parse_int(row.get('Transactions') or row.get('# of Transactions')),
                avg_transaction=parse_float(row.get('Average Transactions') or row.get('AVG Transaction')),
                avg_transaction_time=parse_str(row.get('Average Transaction Time') or row.get('AVG Transaction Time')),
                promotions=parse_float(row.get('Total Promotions') or row.get('Promotions')),
                discounts=parse_float(row.get('Pre-Tax Discounts') or row.get('Discounts')),
                cash_tendered=parse_float(row.get('Total Sales by Cash') or row.get('Cash Tendered')),
                credit_tendered=parse_float(row.get('Total Sales by Credit') or row.get('Credit Tendered')),
                blazepay_tendered=parse_float(row.get('Total Sales by BLAZEPAY') or row.get('BLAZEPay Tendered')),
                ach_tendered=parse_float(row.get('Total Sales by ACH') or row.get('ACH Tendered')),
                cashless_atm_tendered=parse_float(row.get('Total Sales by Cashless ATM') or row.get('CashlessAtm Tendered')),
                tips=parse_float(row.get('Tips')),
                cogs=parse_float(row.get('COGS')),
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
    final_count = await db.scalar(select(func.count(EmployeePerformance.id)))
    return {"table": "employee_performance", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_employee_activity(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest employee_activity.csv."""
    import os
    final_path = csv_path or CSV_PATHS_EMPLOYEES["employee_activity"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting employee activity from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, EmployeeActivity, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            time_val = parse_datetime(row.get('Time'))
            employee = parse_str(row.get('Employee'))
            action = parse_str(row.get('Action'))
            category = parse_str(row.get('Category'))

            line_hash = generate_hash(time_val, employee, action, category)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = EmployeeActivity(
                line_hash=line_hash,
                time=time_val,
                employee=employee,
                action=action,
                category=category,
                terminal=parse_str(row.get('Terminal')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1

            if inserted % 1000 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(EmployeeActivity.id)))
    return {"table": "employee_activity", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_time_clock(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest time_clock_reports.csv."""
    import os
    final_path = csv_path or CSV_PATHS_EMPLOYEES["time_clock"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting time clock from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, TimeClock, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            employee = parse_str(row.get('Employee'))
            clock_in = parse_datetime(row.get('Clock In'))

            line_hash = generate_hash(date_val, employee, clock_in)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = TimeClock(
                line_hash=line_hash,
                date=date_val,
                employee=employee,
                clock_in=clock_in,
                terminal_in=parse_str(row.get('Terminal In')),
                clock_out=parse_datetime(row.get('Clock Out')),
                terminal_out=parse_str(row.get('Terminal Out')),
                time_clocked_in=parse_str(row.get('Time Clocked In(HH:MM:SS)')),
                ipad_sessions=parse_int(row.get('iPad Sessions')),
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
    final_count = await db.scalar(select(func.count(TimeClock.id)))
    return {"table": "time_clock", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}
