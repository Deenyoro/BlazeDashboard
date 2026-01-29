import pandas as pd
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.models.transaction import Transaction, Member, Employee, Product, ProductSale, InventorySnapshot, DiscountUsage
from datetime import date as date_type
from typing import Optional, Dict, Any, Set
import logging
import hashlib

logger = logging.getLogger(__name__)

# CSV column name mappings - handles variations in Blaze exports
COLUMN_MAPPINGS = {
    # Primary identifiers
    "blaze_trans_id": ["Trans ID", "Transaction Id", "TransID"],
    "trans_no": ["Trans No", "Transaction #", "TransNo"],

    # Dates
    "date": ["Date"],
    "created_date": ["Created Date"],
    "prepared_date": ["Prepared Date"],
    "packed_date": ["Packed Date"],
    "start_date": ["Start Date"],
    "end_date": ["End Date"],
    "delivery_date": ["Delivery Date"],

    # Location
    "shop": ["Shop"],
    "company": ["Company"],
    "terminal": ["Terminal"],
    "region": ["Region"],
    "delivery_city": ["Delivery City"],

    # Transaction info
    "trans_type": ["Trans Type", "Transaction Type"],
    "trans_status": ["Trans Status", "Transaction Status"],
    "queue_type": ["Queue Type"],
    "order_source": ["Order Source"],

    # Member
    "member_id_raw": ["Member ID"],
    "member_name": ["Member", "Member Name"],
    "member_group": ["Member Group"],
    "consumer_tax_type": ["Consumer Tax Type"],

    # Financial - Sales
    "retail_value": ["Retail Value of Sales"],
    "gross_sales": ["Gross Sales"],
    "net_sales": ["Net Sales"],
    "net_sales_wo_fees": ["Net Sales w/o Fees"],
    "delivery_fees": ["Delivery Fees"],

    # Discounts
    "pre_tax_discounts": ["Pre Tax Discounts", "Pre-Tax Discounts"],
    "after_tax_discount": ["After Tax Discount"],
    "product_promotions": ["Product Promotions"],
    "cart_promotions": ["Cart Promotions"],
    "discount_notes": ["Discount Notes"],

    # Pre-taxes
    "pre_al_excise_tax": ["Pre AL Excise Tax"],
    "pre_nal_excise_tax": ["Pre NAL Excise Tax"],
    "pre_city_tax": ["Pre City Tax"],
    "pre_county_tax": ["Pre County Tax"],
    "pre_state_tax": ["Pre State Tax"],
    "pre_fed_tax": ["Pre Fed Tax"],

    # Post-taxes
    "post_al_excise_tax": ["Post AL Excise Tax"],
    "post_nal_excise_tax": ["Post NAL Excise Tax"],
    "city_tax": ["City Tax"],
    "county_tax": ["County Tax"],
    "state_tax": ["State Tax"],
    "federal_tax": ["Federal Tax"],

    # Delivery fee taxes
    "delivery_fee_excise_tax": ["Delivery Fee Excise Tax"],
    "city_delivery_fee_tax": ["City Delivery Fee Tax"],
    "county_delivery_fee_tax": ["County Delivery Fee Tax"],
    "state_delivery_fee_tax": ["State Delivery Fee Tax"],
    "fed_delivery_fee_tax": ["Fed Delivery Fee Tax"],

    # Totals
    "total_tax": ["Total Tax"],
    "rounded_amount": ["Rounded Amount"],
    "adjustments": ["Adjustments"],
    "payment_fee": ["Payment Fee"],
    "total_due": ["Total Due"],
    "surcharge_fee_tax": ["Surcharge Fee Tax"],
    "untaxed_fee": ["Untaxed Fee"],

    # Tips & COGS
    "tips": ["Tips"],
    "blazepay_tips": ["BLAZEPAY Tips"],
    "cogs": ["COGS"],

    # Payment
    "payment_type": ["Payment Type"],
    "blazepay_id": ["BLAZEPAY ID"],
    "payment_tendered": ["Payment Tendered"],
    "cash_change": ["Cash Change"],
    "cashless_atm_change": ["Cashless ATM Change"],
    "change_due": ["Change Due"],

    # Employees
    "sold_by": ["Sold By"],
    "employee": ["Employee"],
    "created_by": ["Created By"],
    "prepared_by": ["Prepared By"],
    "packed_by": ["Packed By"],

    # Marketing
    "marketing_source": ["Marketing Source"],
    "order_tags": ["Order Tags"],

    # Loyalty
    "loyalty_points_spent": ["Loyalty Points Spent"],
    "loyalty_points_earned": ["Loyalty Points Earned"],

    # Compliance
    "compliance_system": ["Compliance System"],
    "compliance_order_id": ["Compliance Order ID"],
    "compliance_delivery_id": ["Compliance Delivery ID"],
    "compliance_delivery_ledger_id": ["Compliance Delivery Ledger ID"],
    "compliance_delivery_submit_status": ["Compliance Delivery Submit Status"],
    "submission_error": ["Submission Error"],
}


def get_column_value(row: pd.Series, field: str, csv_columns: set) -> Any:
    """Get value from row using column mapping, trying multiple possible names."""
    possible_names = COLUMN_MAPPINGS.get(field, [field])
    for name in possible_names:
        if name in csv_columns and name in row.index:
            return row[name]
    return None


def parse_datetime(val) -> Optional[datetime]:
    """Parse datetime from CSV, handling various formats and empty values."""
    if pd.isna(val) or val == "" or val is None:
        return None
    try:
        if isinstance(val, datetime):
            return val
        val_str = str(val)
        # Handle epoch-like dates (invalid dates)
        if "1969-12-31" in val_str or "1970-01-01" in val_str:
            return None
        return pd.to_datetime(val)
    except Exception:
        return None


def parse_float(val) -> float:
    """Parse float from CSV, handling empty values and currency formatting."""
    if pd.isna(val) or val == "" or val is None:
        return 0.0
    try:
        # Handle currency formatting
        if isinstance(val, str):
            val = val.replace("$", "").replace(",", "").strip()
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def parse_str(val) -> Optional[str]:
    """Parse string from CSV, handling empty values."""
    if pd.isna(val) or val == "" or val is None:
        return None
    return str(val).strip()


def generate_row_hash(row_data: Dict[str, Any]) -> str:
    """Generate a hash of the row data for change detection."""
    # Use key financial fields for hash
    hash_fields = [
        str(row_data.get("blaze_trans_id", "")),
        str(row_data.get("date", "")),
        str(row_data.get("total_due", 0)),
        str(row_data.get("gross_sales", 0)),
        str(row_data.get("trans_type", "")),
        str(row_data.get("trans_status", "")),
    ]
    hash_string = "|".join(hash_fields)
    return hashlib.md5(hash_string.encode()).hexdigest()


async def get_existing_trans_ids(db: AsyncSession) -> Set[str]:
    """Get all existing transaction IDs from database."""
    result = await db.execute(select(Transaction.blaze_trans_id))
    return {row[0] for row in result.all() if row[0]}


async def get_or_create_member(
    db: AsyncSession,
    blaze_member_id: str,
    name: str,
    member_group: str,
    consumer_tax_type: str,
    member_cache: Dict[str, str]
) -> Optional[str]:
    """Get or create a member record, return member ID."""
    if not blaze_member_id:
        return None

    if blaze_member_id in member_cache:
        return member_cache[blaze_member_id]

    result = await db.execute(
        select(Member).where(Member.blaze_member_id == blaze_member_id)
    )
    member = result.scalar_one_or_none()

    if not member:
        member = Member(
            blaze_member_id=blaze_member_id,
            name=name,
            member_group=member_group,
            consumer_tax_type=consumer_tax_type,
        )
        db.add(member)
        await db.flush()

    member_cache[blaze_member_id] = member.id
    return member.id


async def get_or_create_employee(
    db: AsyncSession,
    name: str,
    employee_cache: Dict[str, str]
) -> Optional[str]:
    """Get or create an employee record, return employee ID."""
    if not name:
        return None

    if name in employee_cache:
        return employee_cache[name]

    result = await db.execute(select(Employee).where(Employee.name == name))
    employee = result.scalar_one_or_none()

    if not employee:
        employee = Employee(name=name)
        db.add(employee)
        await db.flush()

    employee_cache[name] = employee.id
    return employee.id


async def ingest_csv(db: AsyncSession, csv_path: str, force_reimport: bool = False) -> dict:
    """
    Ingest transactions from CSV file into database.

    DEDUPLICATION LOGIC:
    - Uses blaze_trans_id (Trans ID) as the unique identifier
    - Checks against existing database records before insert
    - Skips any transaction that already exists
    - Reports exact counts of new vs skipped records

    Args:
        db: Database session
        csv_path: Path to CSV file
        force_reimport: If True, will update existing records (use with caution)

    Returns:
        Dict with ingestion statistics
    """
    logger.info(f"Starting CSV ingestion from {csv_path}")
    logger.info(f"Force reimport: {force_reimport}")

    # Load CSV
    df = pd.read_csv(csv_path, low_memory=False, encoding='utf-8-sig')
    csv_columns = set(df.columns)
    total_rows = len(df)

    logger.info(f"CSV loaded: {total_rows} rows, {len(csv_columns)} columns")
    logger.info(f"CSV columns: {sorted(csv_columns)}")

    # Get existing transaction IDs for deduplication
    existing_trans_ids = await get_existing_trans_ids(db)
    logger.info(f"Existing transactions in DB: {len(existing_trans_ids)}")

    # Statistics
    inserted = 0
    skipped_duplicate = 0
    skipped_no_id = 0
    errors = 0
    error_details = []

    # Caches
    member_cache: Dict[str, str] = {}
    employee_cache: Dict[str, str] = {}

    # Pre-load existing members and employees
    members_result = await db.execute(select(Member.blaze_member_id, Member.id))
    for row in members_result.all():
        if row[0]:
            member_cache[row[0]] = row[1]

    employees_result = await db.execute(select(Employee.name, Employee.id))
    for row in employees_result.all():
        if row[0]:
            employee_cache[row[0]] = row[1]

    logger.info(f"Loaded {len(member_cache)} members, {len(employee_cache)} employees from cache")

    # Process rows
    batch_size = 500
    for idx, row in df.iterrows():
        try:
            # Get transaction ID - THIS IS THE UNIQUE KEY
            blaze_trans_id = parse_str(get_column_value(row, "blaze_trans_id", csv_columns))

            if not blaze_trans_id:
                skipped_no_id += 1
                continue

            # DEDUPLICATION CHECK - Skip if already exists
            if blaze_trans_id in existing_trans_ids:
                skipped_duplicate += 1
                continue

            # Parse all fields
            date_val = parse_datetime(get_column_value(row, "date", csv_columns))
            if not date_val:
                errors += 1
                error_details.append(f"Row {idx}: Missing or invalid date")
                continue

            # Get member
            member_id_raw = parse_str(get_column_value(row, "member_id_raw", csv_columns))
            member_db_id = None
            if member_id_raw:
                member_db_id = await get_or_create_member(
                    db,
                    member_id_raw,
                    parse_str(get_column_value(row, "member_name", csv_columns)),
                    parse_str(get_column_value(row, "member_group", csv_columns)),
                    parse_str(get_column_value(row, "consumer_tax_type", csv_columns)),
                    member_cache
                )

            # Get employees
            sold_by_name = parse_str(get_column_value(row, "sold_by", csv_columns))
            sold_by_id = await get_or_create_employee(db, sold_by_name, employee_cache) if sold_by_name else None

            created_by_name = parse_str(get_column_value(row, "created_by", csv_columns))
            created_by_id = await get_or_create_employee(db, created_by_name, employee_cache) if created_by_name else None

            # Create transaction record
            transaction = Transaction(
                blaze_trans_id=blaze_trans_id,
                trans_no=parse_str(get_column_value(row, "trans_no", csv_columns)),
                date=date_val,
                created_date=parse_datetime(get_column_value(row, "created_date", csv_columns)),
                prepared_date=parse_datetime(get_column_value(row, "prepared_date", csv_columns)),
                packed_date=parse_datetime(get_column_value(row, "packed_date", csv_columns)),
                start_date=parse_datetime(get_column_value(row, "start_date", csv_columns)),
                end_date=parse_datetime(get_column_value(row, "end_date", csv_columns)),
                delivery_date=parse_datetime(get_column_value(row, "delivery_date", csv_columns)),
                shop=parse_str(get_column_value(row, "shop", csv_columns)),
                company=parse_str(get_column_value(row, "company", csv_columns)),
                terminal=parse_str(get_column_value(row, "terminal", csv_columns)),
                region=parse_str(get_column_value(row, "region", csv_columns)),
                delivery_city=parse_str(get_column_value(row, "delivery_city", csv_columns)),
                trans_type=parse_str(get_column_value(row, "trans_type", csv_columns)),
                trans_status=parse_str(get_column_value(row, "trans_status", csv_columns)),
                queue_type=parse_str(get_column_value(row, "queue_type", csv_columns)),
                order_source=parse_str(get_column_value(row, "order_source", csv_columns)),
                member_id=member_db_id,
                retail_value=parse_float(get_column_value(row, "retail_value", csv_columns)),
                gross_sales=parse_float(get_column_value(row, "gross_sales", csv_columns)),
                net_sales=parse_float(get_column_value(row, "net_sales", csv_columns)),
                net_sales_wo_fees=parse_float(get_column_value(row, "net_sales_wo_fees", csv_columns)),
                delivery_fees=parse_float(get_column_value(row, "delivery_fees", csv_columns)),
                pre_tax_discounts=parse_float(get_column_value(row, "pre_tax_discounts", csv_columns)),
                after_tax_discount=parse_float(get_column_value(row, "after_tax_discount", csv_columns)),
                product_promotions=parse_str(get_column_value(row, "product_promotions", csv_columns)),
                cart_promotions=parse_str(get_column_value(row, "cart_promotions", csv_columns)),
                discount_notes=parse_str(get_column_value(row, "discount_notes", csv_columns)),
                pre_al_excise_tax=parse_float(get_column_value(row, "pre_al_excise_tax", csv_columns)),
                pre_nal_excise_tax=parse_float(get_column_value(row, "pre_nal_excise_tax", csv_columns)),
                pre_city_tax=parse_float(get_column_value(row, "pre_city_tax", csv_columns)),
                pre_county_tax=parse_float(get_column_value(row, "pre_county_tax", csv_columns)),
                pre_state_tax=parse_float(get_column_value(row, "pre_state_tax", csv_columns)),
                pre_fed_tax=parse_float(get_column_value(row, "pre_fed_tax", csv_columns)),
                post_al_excise_tax=parse_float(get_column_value(row, "post_al_excise_tax", csv_columns)),
                post_nal_excise_tax=parse_float(get_column_value(row, "post_nal_excise_tax", csv_columns)),
                city_tax=parse_float(get_column_value(row, "city_tax", csv_columns)),
                county_tax=parse_float(get_column_value(row, "county_tax", csv_columns)),
                state_tax=parse_float(get_column_value(row, "state_tax", csv_columns)),
                federal_tax=parse_float(get_column_value(row, "federal_tax", csv_columns)),
                delivery_fee_excise_tax=parse_float(get_column_value(row, "delivery_fee_excise_tax", csv_columns)),
                city_delivery_fee_tax=parse_float(get_column_value(row, "city_delivery_fee_tax", csv_columns)),
                county_delivery_fee_tax=parse_float(get_column_value(row, "county_delivery_fee_tax", csv_columns)),
                state_delivery_fee_tax=parse_float(get_column_value(row, "state_delivery_fee_tax", csv_columns)),
                fed_delivery_fee_tax=parse_float(get_column_value(row, "fed_delivery_fee_tax", csv_columns)),
                total_tax=parse_float(get_column_value(row, "total_tax", csv_columns)),
                rounded_amount=parse_float(get_column_value(row, "rounded_amount", csv_columns)),
                adjustments=parse_float(get_column_value(row, "adjustments", csv_columns)),
                payment_fee=parse_float(get_column_value(row, "payment_fee", csv_columns)),
                total_due=parse_float(get_column_value(row, "total_due", csv_columns)),
                surcharge_fee_tax=parse_float(get_column_value(row, "surcharge_fee_tax", csv_columns)),
                untaxed_fee=parse_float(get_column_value(row, "untaxed_fee", csv_columns)),
                tips=parse_float(get_column_value(row, "tips", csv_columns)),
                blazepay_tips=parse_float(get_column_value(row, "blazepay_tips", csv_columns)),
                cogs=parse_float(get_column_value(row, "cogs", csv_columns)),
                payment_type=parse_str(get_column_value(row, "payment_type", csv_columns)),
                blazepay_id=parse_str(get_column_value(row, "blazepay_id", csv_columns)),
                payment_tendered=parse_float(get_column_value(row, "payment_tendered", csv_columns)),
                cash_change=parse_float(get_column_value(row, "cash_change", csv_columns)),
                cashless_atm_change=parse_float(get_column_value(row, "cashless_atm_change", csv_columns)),
                change_due=parse_float(get_column_value(row, "change_due", csv_columns)),
                sold_by_id=sold_by_id,
                sold_by_name=sold_by_name,
                created_by_id=created_by_id,
                created_by_name=created_by_name,
                prepared_by=parse_str(get_column_value(row, "prepared_by", csv_columns)),
                packed_by=parse_str(get_column_value(row, "packed_by", csv_columns)),
                marketing_source=parse_str(get_column_value(row, "marketing_source", csv_columns)),
                order_tags=parse_str(get_column_value(row, "order_tags", csv_columns)),
                loyalty_points_spent=parse_float(get_column_value(row, "loyalty_points_spent", csv_columns)),
                loyalty_points_earned=parse_float(get_column_value(row, "loyalty_points_earned", csv_columns)),
                compliance_system=parse_str(get_column_value(row, "compliance_system", csv_columns)),
                compliance_order_id=parse_str(get_column_value(row, "compliance_order_id", csv_columns)),
                compliance_delivery_id=parse_str(get_column_value(row, "compliance_delivery_id", csv_columns)),
                compliance_delivery_ledger_id=parse_str(get_column_value(row, "compliance_delivery_ledger_id", csv_columns)),
                compliance_delivery_submit_status=parse_str(get_column_value(row, "compliance_delivery_submit_status", csv_columns)),
                submission_error=parse_str(get_column_value(row, "submission_error", csv_columns)),
            )

            db.add(transaction)
            existing_trans_ids.add(blaze_trans_id)  # Add to set to prevent in-batch duplicates
            inserted += 1

            # Commit in batches
            if inserted % batch_size == 0:
                await db.commit()
                logger.info(f"Progress: {inserted} inserted, {skipped_duplicate} duplicates skipped")

        except Exception as e:
            errors += 1
            error_details.append(f"Row {idx}: {str(e)}")
            logger.error(f"Error processing row {idx}: {e}")
            continue

    # Final commit
    await db.commit()

    # Validation - count records in DB
    final_count = await db.scalar(select(func.count(Transaction.id)))

    result = {
        "status": "complete",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped_duplicate,
        "skipped_no_id": skipped_no_id,
        "errors": errors,
        "error_details": error_details[:10] if error_details else [],  # Limit error details
        "total_in_db": final_count,
        "validation": {
            "expected_minimum": inserted,
            "actual_count": final_count,
            "passed": final_count >= inserted
        }
    }

    logger.info(f"Ingestion complete: {result}")
    return result


async def get_last_transaction_date(db: AsyncSession) -> Optional[datetime]:
    """Get the date of the most recent transaction in the database."""
    result = await db.execute(
        select(func.max(Transaction.date))
    )
    return result.scalar()


async def validate_no_duplicates(db: AsyncSession) -> dict:
    """Validate there are no duplicate transactions in the database."""
    # Check for duplicate blaze_trans_id
    duplicate_query = text("""
        SELECT blaze_trans_id, COUNT(*) as cnt
        FROM transactions
        GROUP BY blaze_trans_id
        HAVING COUNT(*) > 1
    """)
    result = await db.execute(duplicate_query)
    duplicates = result.all()

    return {
        "has_duplicates": len(duplicates) > 0,
        "duplicate_count": len(duplicates),
        "duplicate_ids": [row[0] for row in duplicates[:10]]  # Show first 10
    }
