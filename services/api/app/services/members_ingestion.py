"""Ingestion for member data: performance, inactive, marketing."""

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.models.members_extended import MemberPerformance, InactiveMember, MarketingContact
from app.services.reports_ingestion import (
    parse_date, parse_datetime, parse_float, parse_int,
    parse_str, generate_hash, get_existing_hashes, DATA_DIR
)

logger = logging.getLogger(__name__)

CSV_PATHS_MEMBERS = {
    "member_performance": f"{DATA_DIR}/member_performance.csv",
    "inactive_members": f"{DATA_DIR}/inactive_members.csv",
    "marketing": f"{DATA_DIR}/marketing.csv",
}


async def ingest_member_performance(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest member_performance.csv."""
    import os
    final_path = csv_path or CSV_PATHS_MEMBERS["member_performance"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting member performance from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    result = await db.execute(select(MemberPerformance.member_id))
    existing = {r[0] for r in result.all() if r[0]}
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            member_id = parse_str(row.get('MemberId'))
            if not member_id or member_id in existing:
                skipped += 1
                continue

            record = MemberPerformance(
                member_id=member_id,
                member_name=parse_str(row.get('Member Name')),
                member_phone=parse_str(row.get('Member Phone')),
                marketing_src=parse_str(row.get('Marketing Src')),
                member_group=parse_str(row.get('Member Group')),
                date_joined=parse_datetime(row.get('Date Joined')),
                consumer_type=parse_str(row.get('Consumer Type')),
                loyalty_points=parse_float(row.get('Loyalty Points')),
                state=parse_str(row.get('State')),
                zip_code=parse_str(row.get('Zip Code')),
                last_visited=parse_datetime(row.get('Last Visited')),
                num_visits=parse_int(row.get('# of Visits')),
                num_sales=parse_int(row.get('# of Sales')),
                num_refunds=parse_int(row.get('# of Refunds')),
                gross_sales_receipts=parse_float(row.get('Gross Sales Receipts')),
                gross_refund_receipts=parse_float(row.get('Gross Refund Receipts')),
                avg_sales_receipts=parse_float(row.get('Avg Sales Receipts')),
                avg_refund_receipts=parse_float(row.get('Avg Refund Receipts')),
            )
            db.add(record)
            existing.add(member_id)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(MemberPerformance.id)))
    return {"table": "member_performance", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_inactive_members(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest inactive_members.csv."""
    import os
    final_path = csv_path or CSV_PATHS_MEMBERS["inactive_members"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting inactive members from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, InactiveMember, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            first = parse_str(row.get('First Name'))
            last = parse_str(row.get('Last Name'))
            last_visit = parse_str(row.get('Last Visit'))

            line_hash = generate_hash(first, last, last_visit)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = InactiveMember(
                line_hash=line_hash,
                first_name=first,
                last_name=last,
                cell_phone=parse_str(row.get('Cell Phone')),
                email=parse_str(row.get('Email')),
                last_visit=parse_datetime(row.get('Last Visit')),
                rec_exp_date=parse_date(row.get('Rec. Exp. Date')),
                total_amount_spent=parse_float(row.get('Total Amount Spent')),
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
    final_count = await db.scalar(select(func.count(InactiveMember.id)))
    return {"table": "inactive_members", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_marketing(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest marketing.csv."""
    import os
    final_path = csv_path or CSV_PATHS_MEMBERS["marketing"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting marketing contacts from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, MarketingContact, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            first = parse_str(row.get('First Name'))
            last = parse_str(row.get('Last Name'))
            email = parse_str(row.get('Email'))

            line_hash = generate_hash(first, last, email)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = MarketingContact(
                line_hash=line_hash,
                first_name=first,
                last_name=last,
                membership_group=parse_str(row.get('Membership Group')),
                marketing_source=parse_str(row.get('Marketing Source')),
                email=email,
                loyalty_points=parse_float(row.get('Loyalty Points')),
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
    final_count = await db.scalar(select(func.count(MarketingContact.id)))
    return {"table": "marketing_contacts", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}
