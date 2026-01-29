"""Ingestion for entity master data: vendors, product catalog, batches, consumers."""

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.models.entities import Vendor, ProductCatalog, ProductBatch, Consumer
from app.services.reports_ingestion import (
    get_csv_path, parse_date, parse_datetime, parse_float, parse_int,
    parse_str, parse_bool, generate_hash, get_existing_hashes, DATA_DIR
)

logger = logging.getLogger(__name__)

CSV_PATHS_ENTITIES = {
    "vendors": f"{DATA_DIR}/vendors_export.csv",
    "product_catalog": f"{DATA_DIR}/company_products_export.csv",
    "product_batches": f"{DATA_DIR}/company_product_batch_export.csv",
    "consumers": f"{DATA_DIR}/consumer_export.csv",
}


async def ingest_vendors(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest vendors_export.csv."""
    final_path = csv_path or CSV_PATHS_ENTITIES["vendors"]
    import os
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting vendors from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    result = await db.execute(select(Vendor.vendor_name))
    existing = {r[0] for r in result.all() if r[0]}
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            name = parse_str(row.get('Vendor Name'))
            if not name or name in existing:
                skipped += 1
                continue

            record = Vendor(
                vendor_name=name,
                contact_first_name=parse_str(row.get('Contact First Name')),
                contact_last_name=parse_str(row.get('Contact Last Name')),
                phone=parse_str(row.get('Phone')),
                email=parse_str(row.get('Email')),
                fax=parse_str(row.get('Fax')),
                active=parse_bool(row.get('Active'), true_val='Yes'),
                website=parse_str(row.get('Website')),
                street_address=parse_str(row.get('Street Address')),
                city=parse_str(row.get('City')),
                state=parse_str(row.get('State')),
                zip_code=parse_str(row.get('Zip Code')),
                description=parse_str(row.get('Description')),
                company_type=parse_str(row.get('Company Type')),
                vendor_type=parse_str(row.get('Vendor Type')),
                license_type=parse_str(row.get('License Type')),
                license_number=parse_str(row.get('License Number')),
            )
            db.add(record)
            existing.add(name)
            inserted += 1
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(Vendor.id)))
    return {"table": "vendors", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_product_catalog(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest company_products_export.csv."""
    final_path = csv_path or CSV_PATHS_ENTITIES["product_catalog"]
    import os
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting product catalog from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    result = await db.execute(select(ProductCatalog.sku))
    existing = {r[0] for r in result.all() if r[0]}
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            sku = parse_str(row.get('SKU'))
            if not sku or sku in existing:
                skipped += 1
                continue

            record = ProductCatalog(
                shop=parse_str(row.get('Shop')),
                sku=sku,
                item=parse_str(row.get('Item')),
                category=parse_str(row.get('Category')),
                cannabis=parse_str(row.get('Cannabis')),
                measurement=parse_str(row.get('Measurement')),
                low_inventory_threshold=parse_float(row.get('Low Inventory Threshold')),
                cost_per_unit=parse_float(row.get('Cost per Unit')),
                wholesale_cost=parse_float(row.get('Wholesale cost')),
                unit_price=parse_float(row.get('Unit Price')),
                unit_sale_price=parse_float(row.get('Unit Sale Price')),
                half_unit_price=parse_float(row.get('.5 Unit Price')),
                half_unit_sale_price=parse_float(row.get('.5 Unit Sale Price')),
                two_units_price=parse_float(row.get('2 Units Price')),
                two_units_sale_price=parse_float(row.get('2 Units Sale Price')),
                gram_price=parse_float(row.get('Gram Price')),
                gram_sale_price=parse_float(row.get('Gram Sale Price')),
                eighth_price=parse_float(row.get('1/8th Price')),
                eighth_sale_price=parse_float(row.get('1/8th Sale Price')),
                quarter_price=parse_float(row.get('1/4th Price')),
                quarter_sale_price=parse_float(row.get('1/4th Sale Price')),
                half_price=parse_float(row.get('1/2 Price')),
                half_sale_price=parse_float(row.get('1/2 Sale Price')),
                oz_price=parse_float(row.get('1 Oz Price')),
                oz_sale_price=parse_float(row.get('1 Oz Sale Price')),
                product_type=parse_str(row.get('Type')),
                description=parse_str(row.get('Description')),
                thc_pct=parse_float(row.get('THC %')),
                cbd_pct=parse_float(row.get('CBD %')),
                cbn_pct=parse_float(row.get('CBN %')),
                thca_pct=parse_float(row.get('THCa %')),
                cbda_pct=parse_float(row.get('CBDa %')),
                cbg_pct=parse_float(row.get('CBG %')),
                thc_mg=parse_float(row.get('THC mg')),
                cbd_mg=parse_float(row.get('CBD mg')),
                inventory_available=parse_float(row.get('Inventory Available')),
                date_purchased=parse_date(row.get('Date Purchased')),
                vendor_id_ref=parse_str(row.get('Vendor ID')),
                vendor=parse_str(row.get('Vendor')),
                genetics=parse_str(row.get('Genetics')),
                strain=parse_str(row.get('Strain')),
                product_id=parse_str(row.get('Product ID')),
                brand=parse_str(row.get('Brand')),
                cannabis_type=parse_str(row.get('Cannabis Type')),
                weight_per_unit=parse_float(row.get('Weight Per Unit')),
                active=parse_bool(row.get('Active'), true_val='Yes'),
                available_online=parse_bool(row.get('Available Online'), true_val='Yes'),
                sell_type=parse_str(row.get('Sell Type')),
            )
            db.add(record)
            existing.add(sku)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(ProductCatalog.id)))
    return {"table": "product_catalog", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_product_batches(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest company_product_batch_export.csv."""
    final_path = csv_path or CSV_PATHS_ENTITIES["product_batches"]
    import os
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting product batches from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1, on_bad_lines='skip', quoting=3)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, ProductBatch, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            product_sku = parse_str(row.get('Product SKU'))
            batch_id = parse_str(row.get('Batch ID'))
            received = parse_str(row.get('Received Date'))

            line_hash = generate_hash(product_sku, batch_id, received)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = ProductBatch(
                line_hash=line_hash,
                shop_name=parse_str(row.get('Shop Name')),
                vendor_name=parse_str(row.get('Vendor Name')),
                po_number=parse_str(row.get('PO Number')),
                batch_description=parse_str(row.get('Batch Description')),
                brand=parse_str(row.get('Brand')),
                product_id=parse_str(row.get('Product ID')),
                product_name=parse_str(row.get('Product Name')),
                product_sku=product_sku,
                category=parse_str(row.get('Category')),
                measurement_type=parse_str(row.get('Measurement Type')),
                weight_type=parse_str(row.get('Weight Type')),
                weight=parse_float(row.get('Weight')),
                net_weight=parse_float(row.get('Net Weight')),
                status=parse_str(row.get('Status')),
                archived=parse_bool(row.get('Archived?'), true_val='Yes'),
                cannabis_type=parse_str(row.get('Cannabis Type')),
                batch_id=batch_id,
                metrc_package_label=parse_str(row.get('Metrc Package Label')),
                purchased_qty=parse_float(row.get('Purchased Qty')),
                current_qty=parse_float(row.get('Current Qty')),
                purchased_cost=parse_float(row.get('Purchased Cost')),
                cost_per_unit=parse_float(row.get('Cost per Unit')),
                current_cogs=parse_float(row.get('Current COGS')),
                purchased_date=parse_date(row.get('Purchased Date')),
                sell_by_date=parse_date(row.get('Sell By Date')),
                expiration_date=parse_date(row.get('Expiration Date')),
                received_date=parse_date(row.get('Received Date')),
                total_thc_pct=parse_float(row.get('Total THC (%)')),
                total_cbd_pct=parse_float(row.get('Total CBD (%)')),
                cbn_pct=parse_float(row.get('CBN (%)')),
                thca_pct=parse_float(row.get('THCa (%)')),
                cbda_pct=parse_float(row.get('CBDa (%)')),
                cbg_pct=parse_float(row.get('CBG (%)')),
                total_terpenes=parse_float(row.get('Total Terpenes')),
                unit_excise_tax=parse_float(row.get('Unit Excise Tax')),
                total_excise_tax=parse_float(row.get('Total Excise Tax')),
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
    final_count = await db.scalar(select(func.count(ProductBatch.id)))
    return {"table": "product_batches", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_consumers(db: AsyncSession, csv_path: str = None) -> dict:
    """Ingest consumer_export.csv."""
    final_path = csv_path or CSV_PATHS_ENTITIES["consumers"]
    import os
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting consumers from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    result = await db.execute(select(Consumer.blaze_consumer_id))
    existing = {r[0] for r in result.all() if r[0]}
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            consumer_id = parse_str(row.get('Consumer Id'))
            if not consumer_id or consumer_id in existing:
                skipped += 1
                continue

            record = Consumer(
                blaze_consumer_id=consumer_id,
                first_name=parse_str(row.get('First Name')),
                last_name=parse_str(row.get('Last Name')),
                status=parse_str(row.get('Status')),
                email=parse_str(row.get('Email Address')),
                date_of_birth=parse_date(row.get('Date of Birth')),
                gender=parse_str(row.get('Gender')),
                date_joined=parse_datetime(row.get('Date Joined')),
                is_medical=parse_bool(row.get('Medical?'), true_val='Yes'),
                phone=parse_str(row.get('Primary Phone')),
                street_address1=parse_str(row.get('Street Address1')),
                street_address2=parse_str(row.get('Street Address2')),
                city=parse_str(row.get('City')),
                state=parse_str(row.get('State')),
                zip_code=parse_str(row.get('Zip Code')),
                country=parse_str(row.get('Country')),
                dl_number=parse_str(row.get('DL Number')),
                dl_state=parse_str(row.get('DL State')),
                dl_expiration=parse_date(row.get('DL Expiration Date')),
                rec_number=parse_str(row.get('Recommendation Number')),
                rec_expiration=parse_date(row.get('Recommendation Expiration Date')),
                rec_issue_date=parse_date(row.get('Recommendation Issue Date')),
                marketing_source=parse_str(row.get('Marketing Source')),
                text_opt_in=parse_bool(row.get('Text Opt-In'), true_val='Yes'),
                email_opt_in=parse_bool(row.get('Email Opt-In'), true_val='Yes'),
                consumer_type=parse_str(row.get('Consumer Type')),
            )
            db.add(record)
            existing.add(consumer_id)
            inserted += 1

            if inserted % 500 == 0:
                await db.commit()
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(Consumer.id)))
    return {"table": "consumers", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}
