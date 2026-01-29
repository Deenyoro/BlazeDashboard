"""Ingestion for extended inventory data: aging, distribution, valuation, transfers, etc."""

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.models.sales_extended import (
    InventoryAging, InventoryDistribution, InventoryValuation,
    InventoryTransfer, SellThrough, CurrentInventory,
)
from app.services.reports_ingestion import (
    parse_date, parse_datetime, parse_float, parse_int,
    parse_str, generate_hash, get_existing_hashes, DATA_DIR
)

logger = logging.getLogger(__name__)

CSV_PATHS_INV = {
    "inventory_aging": f"{DATA_DIR}/inventory_aging.csv",
    "inventory_distribution": f"{DATA_DIR}/inventory_distribution.csv",
    "inventory_valuation": f"{DATA_DIR}/inventory_log_valuation.csv",
    "inventory_transfers": f"{DATA_DIR}/inventory_transfer_log.csv",
    "sell_through": f"{DATA_DIR}/sell_through_report.csv",
    "current_inventory": f"{DATA_DIR}/single_inventory.csv",
}


async def ingest_inventory_aging(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_INV["inventory_aging"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting inventory aging from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, InventoryAging, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            sku = parse_str(row.get('Product SKU'))
            name = parse_str(row.get('Product Name'))

            line_hash = generate_hash(sku, name)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = InventoryAging(
                line_hash=line_hash,
                product_sku=sku,
                product_name=name,
                product_category=parse_str(row.get('Product Category')),
                low_inventory_threshold=parse_float(row.get('Low Inventory Threshold')),
                days_0_30_qty=parse_float(row.get('0-30 Days Quantity')),
                days_0_30_val=parse_float(row.get('0-30 Days Valuation')),
                days_31_45_qty=parse_float(row.get('31-45 Days Quantity')),
                days_31_45_val=parse_float(row.get('31-45 Days Valuation')),
                days_46_60_qty=parse_float(row.get('46-60 Days Quantity')),
                days_46_60_val=parse_float(row.get('46-60 Days Valuation')),
                days_61_90_qty=parse_float(row.get('61-90 Days Quantity')),
                days_61_90_val=parse_float(row.get('61-90 Days Valuation')),
                days_90_plus_qty=parse_float(row.get('90 Days + Quantity')),
                days_90_plus_val=parse_float(row.get('90 Days + Valuation')),
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
    final_count = await db.scalar(select(func.count(InventoryAging.id)))
    return {"table": "inventory_aging", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_inventory_distribution(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_INV["inventory_distribution"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting inventory distribution from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, InventoryDistribution, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            product = parse_str(row.get('Product'))
            category = parse_str(row.get('Category'))
            brand = parse_str(row.get('Brand'))

            line_hash = generate_hash(product, category, brand)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = InventoryDistribution(
                line_hash=line_hash,
                product=product,
                category=category,
                brand=brand,
                unit_type=parse_str(row.get('Unit Type')),
                low_inventory_threshold=parse_float(row.get('Low Inventory Threshold')),
                total=parse_float(row.get('Total')),
                exchange=parse_float(row.get('Exchange')),
                fulfillment=parse_float(row.get('Fulfillment')),
                quarantine=parse_float(row.get('Quarantine')),
                safe=parse_float(row.get('Safe')),
                vault=parse_float(row.get('Vault')),
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
    final_count = await db.scalar(select(func.count(InventoryDistribution.id)))
    return {"table": "inventory_distribution", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_inventory_valuation(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_INV["inventory_valuation"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting inventory valuation from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, InventoryValuation, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            name = parse_str(row.get('Product Name')) or parse_str(row.get('Product Category'))
            category = parse_str(row.get('Product Category') or row.get('Category'))
            status = parse_str(row.get('Status'))

            line_hash = generate_hash(name, category, status)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = InventoryValuation(
                line_hash=line_hash,
                product_name=name,
                category=category,
                cannabis_type=parse_str(row.get('Cannabis Type')),
                status=status,
                avg_unit_cost=parse_float(row.get('Avg Unit Cost')),
                avg_excise_cost=parse_float(row.get('Avg. Excise Cost')),
                unit_excise_cost=parse_float(row.get('Unit+Excise Cost')),
                avg_retail_price=parse_float(row.get('Avg Retail Price')),
                avg_profit=parse_float(row.get('Avg Profit')),
                avg_margin_pct=parse_float(row.get('Avg Margin %')),
                avg_markup_pct=parse_float(row.get('Avg Markup %')),
                total_available_qty=parse_float(row.get('Total Available Quantity')),
                total_available_cogs=parse_float(row.get('Total Available COGS')),
                total_available_excise=parse_float(row.get('Total Available Excise')),
                total_available_cogs_excise=parse_float(row.get('Total Available COGS+Excise')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(InventoryValuation.id)))
    return {"table": "inventory_valuation", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_inventory_transfers(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_INV["inventory_transfers"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting inventory transfers from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, InventoryTransfer, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_datetime(row.get('Date'))
            employee = parse_str(row.get('Employee'))
            product = parse_str(row.get('Product'))
            origin = parse_str(row.get('Origin Inventory'))
            dest = parse_str(row.get('Destination'))
            amount = parse_str(row.get('Amount'))

            line_hash = generate_hash(date_val, employee, product, origin, dest, amount)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = InventoryTransfer(
                line_hash=line_hash,
                date=date_val,
                employee=employee,
                product=product,
                origin_shop=parse_str(row.get('Origin Shop')),
                origin_inventory=origin,
                destination_shop=parse_str(row.get('Destination Shop')),
                destination=dest,
                amount=parse_float(row.get('Amount')),
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
    final_count = await db.scalar(select(func.count(InventoryTransfer.id)))
    return {"table": "inventory_transfers", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_sell_through(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_INV["sell_through"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting sell-through from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, SellThrough, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            pid = parse_str(row.get('Product Id'))
            name = parse_str(row.get('Product Name'))

            line_hash = generate_hash(pid, name)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = SellThrough(
                line_hash=line_hash,
                product_id=pid,
                product_name=name,
                category=parse_str(row.get('Category')),
                low_inventory_threshold=parse_float(row.get('Low Inventory Threshold')),
                avg_qty_sold_per_day=parse_float(row.get('Avg Qty Sold Per Day')),
                days_remaining=parse_float(row.get('Days Remaining in Inventory')),
                qty_on_hand=parse_float(row.get('Currenty Quanity On Hand')),
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
    final_count = await db.scalar(select(func.count(SellThrough.id)))
    return {"table": "sell_through", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_current_inventory(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_INV["current_inventory"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting current inventory from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, CurrentInventory, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            product = parse_str(row.get('Product'))
            category = parse_str(row.get('Category'))
            status = parse_str(row.get('Status'))

            line_hash = generate_hash(product, category, status)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = CurrentInventory(
                line_hash=line_hash,
                product=product,
                category=category,
                status=status,
                low_inventory_threshold=parse_float(row.get('Low Inventory Threshold')),
                current_quantity=parse_float(row.get('Current Quantity')),
                current_cogs=parse_float(row.get('Current COGs')),
                sold_quantity=parse_float(row.get('Sold Quantity')),
                sold_cogs=parse_float(row.get('Sold COGs')),
                current_prepackages=parse_float(row.get('Current Prepackages')),
                current_pack_cogs=parse_float(row.get('Current PACK COGs')),
                sold_prepackages=parse_float(row.get('Sold Prepackages')),
                sold_pack_cogs=parse_float(row.get('Sold PACK COGs')),
                retail_price=parse_float(row.get('Retail Price')),
                retail_value=parse_float(row.get('Retail Value')),
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
    final_count = await db.scalar(select(func.count(CurrentInventory.id)))
    return {"table": "current_inventory", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}
