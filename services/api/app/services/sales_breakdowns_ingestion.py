"""Ingestion for sales breakdown reports: by city, hour, product, vendor, consumer type, etc."""

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.models.sales_extended import (
    SalesByCity, SalesByHour, SalesByProduct, SalesByProductCategory,
    SalesByVendor, SalesByConsumerType, EmployeeSalesByProduct,
    ProductsByVendor, ProductSalesByInventory, ProductSellByExpire,
)
from app.services.reports_ingestion import (
    parse_date, parse_float, parse_int,
    parse_str, generate_hash, get_existing_hashes, DATA_DIR
)

logger = logging.getLogger(__name__)

CSV_PATHS_BREAKDOWNS = {
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


async def ingest_sales_by_city(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_BREAKDOWNS["sales_by_city"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting sales by city from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, SalesByCity, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            city = parse_str(row.get('City'))
            state = parse_str(row.get('State'))

            line_hash = generate_hash(city, state)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = SalesByCity(
                line_hash=line_hash,
                city=city,
                state=state,
                transactions=parse_int(row.get('Transactions')),
                subtotal_sales=parse_float(row.get('Subtotal Sales')),
                discount=parse_float(row.get('Discount')),
                total_taxes=parse_float(row.get('Total Taxes')),
                delivery_fee=parse_float(row.get('Delivery Fee')),
                tips=parse_float(row.get('Tips')),
                gross_receipts=parse_float(row.get('Gross Receipts')),
                percentage_of_sales=parse_float(row.get('Percentage of Sales')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(SalesByCity.id)))
    return {"table": "sales_by_city", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_sales_by_consumer_type(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_BREAKDOWNS["sales_by_consumer_type"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting sales by consumer type from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, SalesByConsumerType, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            breakdown = parse_str(row.get('Breakdown'))

            line_hash = generate_hash(breakdown)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = SalesByConsumerType(
                line_hash=line_hash,
                breakdown=breakdown,
                cannabis_retail_value=parse_float(row.get('Cannabis Retail1Value') or row.get('Cannabis Retail Value')),
                non_cannabis_retail_value=parse_float(row.get('Non-Cannabis Retail Value')),
                cannabis_discounts=parse_float(row.get('Cannabis Discounts')),
                non_cannabis_discounts=parse_float(row.get('Non-Cannabis Discounts')),
                total_discounts=parse_float(row.get('Total Discounts')),
                after_tax_discount=parse_float(row.get('After Tax Discount')),
                gross_revenue=parse_float(row.get('Gross Revenue')),
                total_tax=parse_float(row.get('Total Tax')),
                delivery_fees=parse_float(row.get('Delivery Fees')),
                tips=parse_float(row.get('Tips')),
                gross_receipt=parse_float(row.get('Gross Receipt')),
                cogs=parse_float(row.get('COGS')),
                net_profit=parse_float(row.get('Net Profit')),
                num_visits=parse_int(row.get('Number of Visits')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(SalesByConsumerType.id)))
    return {"table": "sales_by_consumer_type", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_sales_by_hour(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_BREAKDOWNS["sales_by_hour"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting sales by hour from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, SalesByHour, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            hour = parse_str(row.get('Hour'))

            line_hash = generate_hash(hour)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = SalesByHour(
                line_hash=line_hash,
                hour=hour,
                recreational_sales=parse_float(row.get('Recreational Sales')),
                medical_sales=parse_float(row.get('Medical Sales')),
                total_sales=parse_float(row.get('Total Sales')),
                recreational_discounts=parse_float(row.get('Recreational Discounts')),
                medicinal_discounts=parse_float(row.get('Medicinal Discounts')),
                total_discounts=parse_float(row.get('Total Discounts')),
                gross_receipts=parse_float(row.get('Gross Receipts')),
                num_transactions=parse_int(row.get('Number of Transactions')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(SalesByHour.id)))
    return {"table": "sales_by_hour", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_sales_by_product(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_BREAKDOWNS["sales_by_product"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting sales by product from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, SalesByProduct, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            product = parse_str(row.get('Product'))
            sku = parse_str(row.get('SKU'))

            line_hash = generate_hash(product, sku)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = SalesByProduct(
                line_hash=line_hash,
                product=product,
                sku=sku,
                category=parse_str(row.get('Category')),
                vendor=parse_str(row.get('Vendor')),
                brand=parse_str(row.get('Brand')),
                product_tags=parse_str(row.get('Product Tags')),
                units_sold=parse_float(row.get('Units Sold')),
                cogs=parse_float(row.get('COGS')),
                retail_value=parse_float(row.get('Retail Value')),
                total_discounts=parse_float(row.get('Total Discounts')),
                product_discounts=parse_float(row.get('Product Discounts')),
                cart_discounts=parse_float(row.get('Cart Discounts')),
                net_sales=parse_float(row.get('Net Sales')),
                subtotal_sales=parse_float(row.get('Subtotal Sales')),
                total_tax=parse_float(row.get('Total Tax')),
                delivery_fees=parse_float(row.get('Delivery Fees')),
                after_tax_discounts=parse_float(row.get('After Tax Discounts')),
                margin=parse_float(row.get('Margin')),
                revenue_per_unit=parse_float(row.get('Revenue/Unit')),
                pct_of_sales=parse_float(row.get('% of Sales')),
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
    final_count = await db.scalar(select(func.count(SalesByProduct.id)))
    return {"table": "sales_by_product", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_sales_by_product_category(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_BREAKDOWNS["sales_by_product_category"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting sales by product category from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, SalesByProductCategory, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            category = parse_str(row.get('Product Category'))

            line_hash = generate_hash(category)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = SalesByProductCategory(
                line_hash=line_hash,
                product_category=category,
                num_trans=parse_int(row.get('# Trans')),
                cogs=parse_float(row.get('COGS')),
                retail_value=parse_float(row.get('Retail Value')),
                total_discounts=parse_float(row.get('Total Discounts')),
                product_discounts=parse_float(row.get('Product Discounts')),
                subtotal_sales=parse_float(row.get('Subtotal Sales')),
                cart_discounts=parse_float(row.get('Cart Discounts')),
                net_sales=parse_float(row.get('Net Sales')),
                total_tax=parse_float(row.get('Total Tax')),
                delivery_fees=parse_float(row.get('Delivery Fees')),
                after_tax_discounts=parse_float(row.get('After Tax Discounts')),
                gross_receipt=parse_float(row.get('Gross Receipt')),
                units_sold=parse_float(row.get('Units Sold')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(SalesByProductCategory.id)))
    return {"table": "sales_by_product_category", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_sales_by_vendor(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_BREAKDOWNS["sales_by_vendor"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting sales by vendor from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, SalesByVendor, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            vendor = parse_str(row.get('Vendor'))
            trans_type = parse_str(row.get('Transaction Type'))

            line_hash = generate_hash(vendor, trans_type)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = SalesByVendor(
                line_hash=line_hash,
                vendor=vendor,
                transaction_type=trans_type,
                subtotal_sales=parse_float(row.get('Subtotal Sales')),
                delivery_fees=parse_float(row.get('Delivery Fees')),
                discounts=parse_float(row.get('Discounts')),
                after_tax_discount=parse_float(row.get('After Tax Discount')),
                tax=parse_float(row.get('Tax')),
                gross_receipt=parse_float(row.get('Gross Receipt')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(SalesByVendor.id)))
    return {"table": "sales_by_vendor", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_employee_sales_by_product(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_BREAKDOWNS["employee_sales_by_product"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting employee sales by product from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, EmployeeSalesByProduct, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            product = parse_str(row.get('Product'))
            employee = parse_str(row.get('Employee'))

            line_hash = generate_hash(product, employee)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = EmployeeSalesByProduct(
                line_hash=line_hash,
                product=product,
                employee=employee,
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
    final_count = await db.scalar(select(func.count(EmployeeSalesByProduct.id)))
    return {"table": "employee_sales_by_product", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_products_by_vendor(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_BREAKDOWNS["products_by_vendor"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting products by vendor from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, ProductsByVendor, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            vendor = parse_str(row.get('Vendor'))
            product = parse_str(row.get('Product'))

            line_hash = generate_hash(vendor, product)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = ProductsByVendor(
                line_hash=line_hash,
                vendor=vendor,
                contact_first_name=parse_str(row.get('Contact First Name')),
                contact_surname=parse_str(row.get('Contact Surname')),
                category=parse_str(row.get('Category')),
                brand=parse_str(row.get('Brand')),
                product=product,
                quantity_sold=parse_float(row.get('Quantity Sold')),
                quantity_in_stock=parse_float(row.get('Quantity In Stock')),
                sales=parse_float(row.get('Sales')),
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
    final_count = await db.scalar(select(func.count(ProductsByVendor.id)))
    return {"table": "products_by_vendor", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_product_sales_by_inventory(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_BREAKDOWNS["product_sales_by_inventory"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting product sales by inventory from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, ProductSalesByInventory, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            product = parse_str(row.get('Product'))
            sku = parse_str(row.get('SKU'))

            line_hash = generate_hash(product, sku)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = ProductSalesByInventory(
                line_hash=line_hash,
                product=product,
                sku=sku,
                category=parse_str(row.get('Category')),
                vendor=parse_str(row.get('Vendor')),
                brand=parse_str(row.get('Brand')),
                product_tags=parse_str(row.get('Product Tags')),
                total_units_sold=parse_float(row.get('Total Units Sold')),
                quarantine_units_sold=parse_float(row.get('Quarantine Units sold')),
                vault_units_sold=parse_float(row.get('Vault Units sold')),
                fulfillment_units_sold=parse_float(row.get('Fulfillment Units sold')),
                exchange_units_sold=parse_float(row.get('Exchange Units sold')),
                sales_floor_units_sold=parse_float(row.get('Sales Floor Units sold')),
                safe_units_sold=parse_float(row.get('Safe Units sold')),
                delivery_units_sold=parse_float(row.get('Delivery Units sold')),
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
    final_count = await db.scalar(select(func.count(ProductSalesByInventory.id)))
    return {"table": "product_sales_by_inventory", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_product_sell_by_expire(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_BREAKDOWNS["product_sell_by_expire"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting product sell-by/expire from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, ProductSellByExpire, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            product_name = parse_str(row.get('Product Name'))
            batch_id = parse_str(row.get('Batch Id'))
            sell_by = parse_str(row.get('Sell By Date'))

            line_hash = generate_hash(product_name, batch_id, sell_by)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = ProductSellByExpire(
                line_hash=line_hash,
                product_category=parse_str(row.get('Product Category')),
                product_name=product_name,
                status=parse_str(row.get('Status')),
                batch_id=batch_id,
                sell_by_date=parse_date(row.get('Sell By Date')),
                qty_remaining=parse_float(row.get('Qty remaining')),
                low_inventory_threshold=parse_float(row.get('Low Inventory Threshold')),
                unit_type=parse_str(row.get('Unit Type')),
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
    final_count = await db.scalar(select(func.count(ProductSellByExpire.id)))
    return {"table": "product_sell_by_expire", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}
