"""
Ingestion service for Completed Sales Details Report CSV.

This CSV format has one row per product sold, with columns like:
- Date, Trans No., Trans Type, Trans Status, Queue Type
- Product SKU, Product Name, Product Category, Brand Name, Vendor
- Member, Member ID, Consumer Tax Type
- Various financial columns (COGs, Retail Value, Net Sales, etc.)
- Various tax columns
- Payment and employee information
- METRC Tag, METRC Sale ID
"""

import pandas as pd
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.models.transaction import Transaction, Member, Employee, Product, ProductSale
from typing import Optional, Dict, Any, Set
import logging
import hashlib

logger = logging.getLogger(__name__)


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
        if "1900" in val_str:
            return None
        return pd.to_datetime(val)
    except Exception:
        return None


def parse_float(val) -> float:
    """Parse float from CSV, handling empty values and currency formatting."""
    if pd.isna(val) or val == "" or val is None:
        return 0.0
    try:
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


def parse_bool(val, true_val="Yes") -> bool:
    """Parse boolean from CSV string."""
    if pd.isna(val):
        return False
    return str(val).strip().lower() == true_val.lower()


def parse_int(val) -> int:
    """Parse int from CSV."""
    if pd.isna(val) or val == "" or val is None:
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def generate_line_hash(row_data: Dict[str, Any]) -> str:
    """Generate a unique hash for a product sale line."""
    # Combine key fields that uniquely identify this line
    hash_fields = [
        str(row_data.get("trans_no", "")),
        str(row_data.get("sale_date", "")),
        str(row_data.get("sku", "")),
        str(row_data.get("product_name", "")),
        str(row_data.get("batch", "")),
        str(row_data.get("metrc_tag", "")),
        str(row_data.get("net_sales", 0)),
        str(row_data.get("quantity", 0)),
    ]
    hash_string = "|".join(hash_fields)
    return hashlib.sha256(hash_string.encode()).hexdigest()


async def get_existing_line_hashes(db: AsyncSession) -> Set[str]:
    """Get all existing line hashes from database."""
    result = await db.execute(select(ProductSale.line_hash))
    return {row[0] for row in result.all() if row[0]}


async def get_or_create_product(
    db: AsyncSession,
    sku: str,
    name: str,
    category: str,
    brand: str,
    product_cache: Dict[str, str]
) -> Optional[str]:
    """Get or create a product record, return product ID."""
    if not sku and not name:
        return None

    cache_key = sku or name
    if cache_key in product_cache:
        return product_cache[cache_key]

    # Try to find by SKU first
    if sku:
        result = await db.execute(
            select(Product).where(Product.sku == sku)
        )
        product = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(Product).where(Product.name == name)
        )
        product = result.scalar_one_or_none()

    if not product:
        product = Product(
            sku=sku,
            name=name or "Unknown",
            category=category,
            brand=brand,
        )
        db.add(product)
        await db.flush()

    product_cache[cache_key] = product.id
    return product.id


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


async def ingest_sales_details_csv(db: AsyncSession, csv_path: str) -> dict:
    """
    Ingest product sales details from the Completed Sales Details Report CSV.

    This CSV has one row per product sold. We:
    1. Create ProductSale records for each line
    2. Aggregate to create/update Transaction records
    3. Create Member, Employee, and Product records as needed

    Deduplication uses a hash of: trans_no + date + sku + product_name + batch + metrc_tag + net_sales + quantity

    Args:
        db: Database session
        csv_path: Path to CSV file

    Returns:
        Dict with ingestion statistics
    """
    logger.info(f"Starting Sales Details CSV ingestion from {csv_path}")

    # Load CSV - skip the first header line ("All Sales Report - ...")
    df = pd.read_csv(csv_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    csv_columns = set(df.columns)
    total_rows = len(df)

    logger.info(f"CSV loaded: {total_rows} rows, {len(csv_columns)} columns")
    logger.info(f"CSV columns: {sorted(csv_columns)}")

    # Get existing line hashes for deduplication
    existing_hashes = await get_existing_line_hashes(db)
    logger.info(f"Existing product sales in DB: {len(existing_hashes)}")

    # Statistics
    inserted = 0
    skipped_duplicate = 0
    skipped_no_trans = 0
    errors = 0
    error_details = []

    # Caches
    product_cache: Dict[str, str] = {}
    member_cache: Dict[str, str] = {}
    employee_cache: Dict[str, str] = {}

    # Pre-load existing caches
    products_result = await db.execute(select(Product.sku, Product.id))
    for row in products_result.all():
        if row[0]:
            product_cache[row[0]] = row[1]

    members_result = await db.execute(select(Member.blaze_member_id, Member.id))
    for row in members_result.all():
        if row[0]:
            member_cache[row[0]] = row[1]

    employees_result = await db.execute(select(Employee.name, Employee.id))
    for row in employees_result.all():
        if row[0]:
            employee_cache[row[0]] = row[1]

    logger.info(f"Loaded {len(product_cache)} products, {len(member_cache)} members, {len(employee_cache)} employees from cache")

    # Column name mapping (CSV column -> our field)
    col_map = {
        'Date': 'sale_date',
        'Trans No.': 'trans_no',
        'Trans Type': 'trans_type',
        'Trans Status': 'trans_status',
        'Queue Type': 'queue_type',
        'Product SKU': 'sku',
        'Product Name': 'product_name',
        'Product Category': 'category',
        'Brand Name': 'brand',
        'Vendor': 'vendor',
        'Member': 'member_name',
        'Consumer Tax Type': 'consumer_tax_type',
        'Cannabis': 'is_cannabis',
        'Quantity Sold': 'quantity',
        'Batch': 'batch',
        'COGs': 'cogs',
        'Retail Value': 'retail_value',
        'Retail Price': 'retail_price',
        'Effective Retail Price': 'effective_retail_price',
        'Net Sales': 'net_sales',
        'Product Discounts': 'product_discounts',
        'Subtotal': 'subtotal',
        'Cart Discounts': 'cart_discounts',
        'Total Discount': 'total_discount',
        'Final Subtotal': 'final_subtotal',
        'Pre ALExcise Tax': 'pre_al_excise_tax',
        'Pre NALExcise Tax': 'pre_nal_excise_tax',
        'Pre Ohio Excise Tax': 'pre_ohio_excise_tax',
        'Pre County Tax': 'pre_county_tax',
        'Pre State Tax': 'pre_state_tax',
        'Pre State Excise Tax': 'pre_state_excise_tax',
        'Post ALExcise Tax': 'post_al_excise_tax',
        'Post NALExcise Tax': 'post_nal_excise_tax',
        'Ohio Excise Tax': 'ohio_excise_tax',
        'County Tax': 'county_tax',
        'State Tax': 'state_tax',
        'State Excise Tax': 'state_excise_tax',
        'Total Tax': 'total_tax',
        'After Tax Discount': 'after_tax_discount',
        'Delivery Fees': 'delivery_fees',
        'Credit Card Fees': 'credit_card_fees',
        'CashlessAtm Fee': 'cashless_atm_fee',
        'ACH Fee': 'ach_fee',
        'BlazePay Fee': 'blazepay_fee',
        'Tips': 'tips',
        'Manual Tips': 'manual_tips',
        'BlazePayID': 'blazepay_id',
        'CashlessAtm Received': 'cashless_atm_received',
        'CashlessAtm Change': 'cashless_atm_change',
        'Cash Received': 'cash_received',
        'Cash Change': 'cash_change',
        'Gross Receipt': 'gross_receipt',
        'Rounded Amount': 'rounded_amount',
        'Employee': 'sold_by',
        'Terminal': 'terminal',
        'Payment Type': 'payment_type',
        'Promotion(s)': 'promotions',
        'Marketing Source': 'marketing_source',
        'Member Group': 'member_group',
        'Zip Code': 'zip_code',
        'Member State': 'member_state',
        'Date Joined': 'date_joined',
        'Gender': 'gender',
        'DOB': 'dob',
        'Age': 'age',
        'Loyalty Points': 'loyalty_points',
        'Created By': 'created_by',
        'Created Date': 'created_date',
        'Prepared By': 'prepared_by',
        'Prepared Date': 'prepared_date',
        'Packed  By': 'packed_by',  # Note: double space in CSV
        'Packed Date': 'packed_date',
        'Member ID': 'member_id',
        'Discount Notes': 'discount_notes',
        'Order Tags': 'order_tags',
        'METRC Tag': 'metrc_tag',
        'METRC Sale ID': 'metrc_sale_id',
        'Region Name': 'region_name',
        'BLAZEPAY': 'blazepay_amount',
        'Cashless ATM': 'cashless_atm_amount',
        'Cash': 'cash_amount',
    }

    def get_val(row, csv_col):
        """Get value from row using CSV column name."""
        if csv_col in row.index:
            return row[csv_col]
        return None

    batch_size = 500

    for idx, row in df.iterrows():
        try:
            # Get transaction number
            trans_no = parse_str(get_val(row, 'Trans No.'))
            if not trans_no:
                skipped_no_trans += 1
                continue

            # Parse date
            sale_date = parse_datetime(get_val(row, 'Date'))
            if not sale_date:
                errors += 1
                error_details.append(f"Row {idx}: Missing or invalid date")
                continue

            # Parse product info
            sku = parse_str(get_val(row, 'Product SKU'))
            product_name = parse_str(get_val(row, 'Product Name'))
            category = parse_str(get_val(row, 'Product Category'))
            brand = parse_str(get_val(row, 'Brand Name'))
            batch = parse_str(get_val(row, 'Batch'))
            metrc_tag = parse_str(get_val(row, 'METRC Tag'))
            net_sales = parse_float(get_val(row, 'Net Sales'))
            quantity = parse_float(get_val(row, 'Quantity Sold'))

            # Build row data for hash
            row_data = {
                'trans_no': trans_no,
                'sale_date': sale_date.isoformat() if sale_date else '',
                'sku': sku,
                'product_name': product_name,
                'batch': batch,
                'metrc_tag': metrc_tag,
                'net_sales': net_sales,
                'quantity': quantity,
            }

            # Generate deduplication hash
            line_hash = generate_line_hash(row_data)

            # DEDUPLICATION CHECK
            if line_hash in existing_hashes:
                skipped_duplicate += 1
                continue

            # Get or create product
            product_id = await get_or_create_product(
                db, sku, product_name, category, brand, product_cache
            )

            # Get or create member
            member_blaze_id = parse_str(get_val(row, 'Member ID'))
            member_db_id = None
            if member_blaze_id:
                member_db_id = await get_or_create_member(
                    db,
                    member_blaze_id,
                    parse_str(get_val(row, 'Member')),
                    parse_str(get_val(row, 'Member Group')),
                    parse_str(get_val(row, 'Consumer Tax Type')),
                    member_cache
                )

            # Get or create employees
            sold_by_name = parse_str(get_val(row, 'Employee'))
            if sold_by_name:
                await get_or_create_employee(db, sold_by_name, employee_cache)

            created_by_name = parse_str(get_val(row, 'Created By'))
            if created_by_name:
                await get_or_create_employee(db, created_by_name, employee_cache)

            # Create ProductSale record
            product_sale = ProductSale(
                trans_no=trans_no,
                metrc_sale_id=parse_str(get_val(row, 'METRC Sale ID')),
                metrc_tag=metrc_tag,
                line_hash=line_hash,
                sale_date=sale_date,
                trans_type=parse_str(get_val(row, 'Trans Type')),
                trans_status=parse_str(get_val(row, 'Trans Status')),
                queue_type=parse_str(get_val(row, 'Queue Type')),
                product_id=product_id,
                product_name=product_name,
                sku=sku,
                category=category,
                brand=brand,
                vendor=parse_str(get_val(row, 'Vendor')),
                batch=batch,
                is_cannabis=parse_bool(get_val(row, 'Cannabis')),
                quantity=quantity,
                cogs=parse_float(get_val(row, 'COGs')),
                retail_value=parse_float(get_val(row, 'Retail Value')),
                retail_price=parse_float(get_val(row, 'Retail Price')),
                effective_retail_price=parse_float(get_val(row, 'Effective Retail Price')),
                net_sales=net_sales,
                product_discounts=parse_float(get_val(row, 'Product Discounts')),
                subtotal=parse_float(get_val(row, 'Subtotal')),
                cart_discounts=parse_float(get_val(row, 'Cart Discounts')),
                total_discount=parse_float(get_val(row, 'Total Discount')),
                final_subtotal=parse_float(get_val(row, 'Final Subtotal')),
                pre_al_excise_tax=parse_float(get_val(row, 'Pre ALExcise Tax')),
                pre_nal_excise_tax=parse_float(get_val(row, 'Pre NALExcise Tax')),
                pre_ohio_excise_tax=parse_float(get_val(row, 'Pre Ohio Excise Tax')),
                pre_county_tax=parse_float(get_val(row, 'Pre County Tax')),
                pre_state_tax=parse_float(get_val(row, 'Pre State Tax')),
                pre_state_excise_tax=parse_float(get_val(row, 'Pre State Excise Tax')),
                post_al_excise_tax=parse_float(get_val(row, 'Post ALExcise Tax')),
                post_nal_excise_tax=parse_float(get_val(row, 'Post NALExcise Tax')),
                ohio_excise_tax=parse_float(get_val(row, 'Ohio Excise Tax')),
                county_tax=parse_float(get_val(row, 'County Tax')),
                state_tax=parse_float(get_val(row, 'State Tax')),
                state_excise_tax=parse_float(get_val(row, 'State Excise Tax')),
                total_tax=parse_float(get_val(row, 'Total Tax')),
                after_tax_discount=parse_float(get_val(row, 'After Tax Discount')),
                delivery_fees=parse_float(get_val(row, 'Delivery Fees')),
                credit_card_fees=parse_float(get_val(row, 'Credit Card Fees')),
                cashless_atm_fee=parse_float(get_val(row, 'CashlessAtm Fee')),
                ach_fee=parse_float(get_val(row, 'ACH Fee')),
                blazepay_fee=parse_float(get_val(row, 'BlazePay Fee')),
                tips=parse_float(get_val(row, 'Tips')),
                manual_tips=parse_float(get_val(row, 'Manual Tips')),
                blazepay_id=parse_str(get_val(row, 'BlazePayID')),
                cashless_atm_received=parse_float(get_val(row, 'CashlessAtm Received')),
                cashless_atm_change=parse_float(get_val(row, 'CashlessAtm Change')),
                cash_received=parse_float(get_val(row, 'Cash Received')),
                cash_change=parse_float(get_val(row, 'Cash Change')),
                gross_receipt=parse_float(get_val(row, 'Gross Receipt')),
                rounded_amount=parse_float(get_val(row, 'Rounded Amount')),
                payment_type=parse_str(get_val(row, 'Payment Type')),
                terminal=parse_str(get_val(row, 'Terminal')),
                sold_by=sold_by_name,
                created_by=created_by_name,
                created_date=parse_datetime(get_val(row, 'Created Date')),
                prepared_by=parse_str(get_val(row, 'Prepared By')),
                prepared_date=parse_datetime(get_val(row, 'Prepared Date')),
                packed_by=parse_str(get_val(row, 'Packed  By')),
                packed_date=parse_datetime(get_val(row, 'Packed Date')),
                promotions=parse_str(get_val(row, 'Promotion(s)')),
                member_name=parse_str(get_val(row, 'Member')),
                member_id=member_blaze_id,
                member_group=parse_str(get_val(row, 'Member Group')),
                consumer_tax_type=parse_str(get_val(row, 'Consumer Tax Type')),
                marketing_source=parse_str(get_val(row, 'Marketing Source')),
                zip_code=parse_str(get_val(row, 'Zip Code')),
                member_state=parse_str(get_val(row, 'Member State')),
                date_joined=parse_datetime(get_val(row, 'Date Joined')),
                gender=parse_str(get_val(row, 'Gender')),
                dob=parse_datetime(get_val(row, 'DOB')),
                age=parse_int(get_val(row, 'Age')),
                loyalty_points=parse_float(get_val(row, 'Loyalty Points')),
                discount_notes=parse_str(get_val(row, 'Discount Notes')),
                order_tags=parse_str(get_val(row, 'Order Tags')),
                region_name=parse_str(get_val(row, 'Region Name')),
                blazepay_amount=parse_float(get_val(row, 'BLAZEPAY')),
                cashless_atm_amount=parse_float(get_val(row, 'Cashless ATM')),
                cash_amount=parse_float(get_val(row, 'Cash')),
            )

            db.add(product_sale)
            existing_hashes.add(line_hash)  # Prevent in-batch duplicates
            inserted += 1

            # Commit in batches
            if inserted % batch_size == 0:
                await db.commit()
                logger.info(f"Progress: {inserted} inserted, {skipped_duplicate} duplicates skipped")

        except Exception as e:
            errors += 1
            error_details.append(f"Row {idx}: {str(e)}")
            logger.error(f"Error processing row {idx}: {e}")
            await db.rollback()
            continue

    # Final commit
    await db.commit()

    # Validation - count records in DB
    final_count = await db.scalar(select(func.count(ProductSale.id)))

    result = {
        "status": "complete",
        "csv_rows": total_rows,
        "inserted": inserted,
        "skipped_duplicate": skipped_duplicate,
        "skipped_no_trans": skipped_no_trans,
        "errors": errors,
        "error_details": error_details[:20] if error_details else [],
        "total_product_sales_in_db": final_count,
        "validation": {
            "expected_minimum": inserted,
            "actual_count": final_count,
            "passed": final_count >= inserted
        }
    }

    logger.info(f"Ingestion complete: {result}")
    return result


async def get_sales_details_stats(db: AsyncSession) -> dict:
    """Get statistics about product sales in the database."""
    total_count = await db.scalar(select(func.count(ProductSale.id)))

    # Date range
    date_range = await db.execute(
        select(
            func.min(ProductSale.sale_date).label("min_date"),
            func.max(ProductSale.sale_date).label("max_date"),
        )
    )
    dates = date_range.one()

    # Category breakdown
    category_counts = await db.execute(
        select(
            ProductSale.category,
            func.count(ProductSale.id).label("count"),
            func.sum(ProductSale.net_sales).label("total_sales"),
        ).group_by(ProductSale.category)
    )

    by_category = {
        row.category or "Unknown": {"count": row.count, "total_sales": float(row.total_sales or 0)}
        for row in category_counts.all()
    }

    # Unique transactions
    unique_trans = await db.scalar(
        select(func.count(func.distinct(ProductSale.trans_no)))
    )

    # Unique products
    unique_products = await db.scalar(
        select(func.count(func.distinct(ProductSale.sku)))
    )

    return {
        "total_product_sales": total_count,
        "unique_transactions": unique_trans,
        "unique_products": unique_products,
        "date_range": {
            "start": dates.min_date.isoformat() if dates.min_date else None,
            "end": dates.max_date.isoformat() if dates.max_date else None,
        },
        "by_category": by_category,
    }
