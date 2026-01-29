"""Ingestion for extended sales data: delivery, canceled, uncomplete, promotions, P&L, etc."""

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.models.sales_extended import (
    DeliverySale, CanceledVoidSale, UncompleteSale, PromotionsActivity,
    ProfitLoss, PurchaseOrderByCategory, ReturnToVendor, RefundHistoryDetail,
    PaidInOutActivity,
)
from app.services.reports_ingestion import (
    parse_date, parse_datetime, parse_float, parse_int,
    parse_str, parse_bool, generate_hash, get_existing_hashes, DATA_DIR
)

logger = logging.getLogger(__name__)

CSV_PATHS_SALES = {
    "delivery_sales": f"{DATA_DIR}/delivery_sales.csv",
    "canceled_void": f"{DATA_DIR}/total_sales_canceled_void_orders.csv",
    "uncomplete": f"{DATA_DIR}/total_sales_with_uncomplete_orders.csv",
    "promotions_activity": f"{DATA_DIR}/promotions_activity.csv",
    "profit_loss": f"{DATA_DIR}/profit_loss_report.csv",
    "purchase_order_by_category": f"{DATA_DIR}/purchase_order_by_category.csv",
    "return_to_vendor": f"{DATA_DIR}/return_to_vendor.csv",
    "refund_history_detail": f"{DATA_DIR}/refund_history.csv",
    "paidinout_activity": f"{DATA_DIR}/paidinout_activity.csv",
}


async def ingest_delivery_sales(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_SALES["delivery_sales"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting delivery sales from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, DeliverySale, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_datetime(row.get('Date'))
            trans_id = parse_str(row.get('Transaction ID'))
            customer = parse_str(row.get('Customer First Name'))

            line_hash = generate_hash(date_val, trans_id, customer)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = DeliverySale(
                line_hash=line_hash,
                date=date_val,
                transaction_id=trans_id,
                metrc_id=parse_str(row.get('Metrc ID')),
                metrc_delivery_id=parse_str(row.get('Metrc Delivery ID')),
                customer_first_name=customer,
                customer_last_name=parse_str(row.get('Customer Last Name')),
                dob=parse_date(row.get('DOB')),
                delivery_address=parse_str(row.get('Delivery Address')),
                city=parse_str(row.get('City')),
                zip_code=parse_str(row.get('Zip')),
                region=parse_str(row.get('Region')),
                employee=parse_str(row.get('Employee')),
                order_source=parse_str(row.get('Order Source')),
                sales=parse_float(row.get('Sales')),
                discounts=parse_float(row.get('Discounts')),
                subtotal=parse_float(row.get('Subtotal')),
                fees=parse_float(row.get('Fees')),
                al_excise=parse_float(row.get('AL Excise')),
                nal_excise=parse_float(row.get('NAL Excise')),
                ohio_excise_tax=parse_float(row.get('Ohio Excise Tax')),
                county_tax=parse_float(row.get('County Tax')),
                state_tax=parse_float(row.get('State tax')),
                state_excise_tax=parse_float(row.get('State Excise Tax')),
                gross_receipts=parse_float(row.get('Gross Receipts')),
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
    final_count = await db.scalar(select(func.count(DeliverySale.id)))
    return {"table": "delivery_sales", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_canceled_void_sales(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_SALES["canceled_void"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting canceled/void sales from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, CanceledVoidSale, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_datetime(row.get('Date'))
            trans_no = parse_str(row.get('Transaction No.'))
            member = parse_str(row.get('Member'))

            line_hash = generate_hash(date_val, trans_no, member)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = CanceledVoidSale(
                line_hash=line_hash,
                date=date_val,
                member=member,
                transaction_no=trans_no,
                trans_type=parse_str(row.get('Trans Type')),
                trans_status=parse_str(row.get('Trans Status')),
                queue_type=parse_str(row.get('Queue Type')),
                member_id=parse_str(row.get('Member ID')),
                cancellation_reason=parse_str(row.get('Cancellation Reason')),
                consumer_tax_type=parse_str(row.get('Consumer Tax Type')),
                cogs=parse_float(row.get('COGs')),
                retail_value=parse_float(row.get('Retail Value')),
                discounts=parse_float(row.get('Discounts')),
                net_sales=parse_float(row.get('Net Sales')),
                total_tax=parse_float(row.get('Total Tax')),
                delivery_fees=parse_float(row.get('Delivery Fees')),
                tips=parse_float(row.get('Tips')),
                after_tax_discount=parse_float(row.get('After Tax Discount')),
                gross_receipt=parse_float(row.get('Gross Receipt')),
                employee=parse_str(row.get('Employee')),
                terminal=parse_str(row.get('Terminal')),
                payment_type=parse_str(row.get('Payment Type')),
                promotions=parse_str(row.get('Promotion(s)')),
                marketing_source=parse_str(row.get('Marketing Source')),
                gross_sales=parse_float(row.get('Gross Sales')),
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
    final_count = await db.scalar(select(func.count(CanceledVoidSale.id)))
    return {"table": "canceled_void_sales", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_uncomplete_sales(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_SALES["uncomplete"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting uncomplete sales from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, UncompleteSale, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_datetime(row.get('Date'))
            trans_no = parse_str(row.get('Transaction No.'))
            member = parse_str(row.get('Member'))

            line_hash = generate_hash(date_val, trans_no, member)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = UncompleteSale(
                line_hash=line_hash,
                date=date_val,
                member=member,
                transaction_no=trans_no,
                trans_type=parse_str(row.get('Trans Type')),
                trans_status=parse_str(row.get('Trans Status')),
                consumer_tax_type=parse_str(row.get('Consumer Tax Type')),
                cogs=parse_float(row.get('COGs')),
                retail_value=parse_float(row.get('Retail Value')),
                discounts=parse_float(row.get('Discounts')),
                total_tax=parse_float(row.get('Total Tax')),
                delivery_fees=parse_float(row.get('Delivery Fees')),
                tips=parse_float(row.get('Tips')),
                after_tax_discount=parse_float(row.get('After Tax Discount')),
                gross_receipt=parse_float(row.get('Gross Receipt')),
                employee=parse_str(row.get('Employee')),
                terminal=parse_str(row.get('Terminal')),
                payment_type=parse_str(row.get('Payment Type')),
                promotions=parse_str(row.get('Promotion(s)')),
                marketing_source=parse_str(row.get('Marketing Source')),
                metrc_id=parse_str(row.get('MetrcId')),
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
    final_count = await db.scalar(select(func.count(UncompleteSale.id)))
    return {"table": "uncomplete_sales", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_promotions_activity(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_SALES["promotions_activity"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting promotions activity from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, PromotionsActivity, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_datetime(row.get('Date'))
            trans_no = parse_str(row.get('Transaction No'))
            promo = parse_str(row.get('Promo/Reward Name'))

            line_hash = generate_hash(date_val, trans_no, promo)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = PromotionsActivity(
                line_hash=line_hash,
                date=date_val,
                transaction_no=trans_no,
                reward_system=parse_str(row.get('Reward System')),
                promo_name=promo,
                promo_type=parse_str(row.get('Type')),
                code_used=parse_str(row.get('Code Used')),
                cash_value=parse_float(row.get('Cash Value')),
                employee=parse_str(row.get('Employee')),
                member=parse_str(row.get('Member')),
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
    final_count = await db.scalar(select(func.count(PromotionsActivity.id)))
    return {"table": "promotions_activity", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_profit_loss(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_SALES["profit_loss"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting profit/loss from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, ProfitLoss, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                continue

            line_hash = generate_hash(date_val)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            # Handle % of Margin - strip % sign
            margin_str = parse_str(row.get('% of Margin'))
            margin_pct = 0.0
            if margin_str:
                margin_pct = parse_float(margin_str.replace('%', ''))

            record = ProfitLoss(
                line_hash=line_hash,
                date=date_val,
                gross_receipts=parse_float(row.get('Gross Receipts')),
                cost=parse_float(row.get('Cost')),
                loss=parse_float(row.get('Loss')),
                profit=parse_float(row.get('Profit')),
                discount=parse_float(row.get('Discount')),
                margin_pct=margin_pct,
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
    final_count = await db.scalar(select(func.count(ProfitLoss.id)))
    return {"table": "profit_loss", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_purchase_order_by_category(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_SALES["purchase_order_by_category"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting purchase orders by category from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, PurchaseOrderByCategory, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            po_date = parse_date(row.get('PO Date'))
            vendor = parse_str(row.get('Vendor Name'))
            category = parse_str(row.get('Product Category') or row.get('Product Category '))
            po_num = parse_str(row.get('PO #'))

            line_hash = generate_hash(po_date, vendor, category, po_num)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = PurchaseOrderByCategory(
                line_hash=line_hash,
                po_date=po_date,
                vendor_name=vendor,
                product_category=category,
                cogs=parse_float(row.get('COGS')),
                excise_tax=parse_float(row.get('Excise Tax')),
                po_number=po_num,
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(PurchaseOrderByCategory.id)))
    return {"table": "purchase_order_by_category", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_return_to_vendor(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_SALES["return_to_vendor"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting return to vendor from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, ReturnToVendor, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            vendor = parse_str(row.get('Vendor'))
            product = parse_str(row.get('Product'))
            batch_sku = parse_str(row.get('Batch SKU'))

            line_hash = generate_hash(date_val, vendor, product, batch_sku)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = ReturnToVendor(
                line_hash=line_hash,
                date=date_val,
                vendor=vendor,
                product_category=parse_str(row.get('Product Category')),
                product=product,
                low_inventory_threshold=parse_float(row.get('Low Inventory Threshold')),
                batch_sku=batch_sku,
                quantity=parse_float(row.get('Quantity')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(ReturnToVendor.id)))
    return {"table": "return_to_vendor", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_refund_history_detail(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_SALES["refund_history_detail"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting refund history detail from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, RefundHistoryDetail, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                continue
            trans_no = parse_str(row.get('Transaction No.'))
            product = parse_str(row.get('Product'))
            amount = parse_str(row.get('Refund Amount'))

            line_hash = generate_hash(date_val, trans_no, product, amount)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = RefundHistoryDetail(
                line_hash=line_hash,
                date=date_val,
                transaction_no=trans_no,
                employee=parse_str(row.get('Employee')),
                customer=parse_str(row.get('Customer')),
                with_inventory=parse_bool(row.get('With Inventory'), true_val='Yes'),
                refund_as=parse_str(row.get('Refund As')),
                refund_amount=parse_float(row.get('Refund Amount')),
                product=product,
                quantity=parse_float(row.get('Quantity')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(RefundHistoryDetail.id)))
    return {"table": "refund_history_detail", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}


async def ingest_paidinout_activity(db: AsyncSession, csv_path: str = None) -> dict:
    import os
    final_path = csv_path or CSV_PATHS_SALES["paidinout_activity"]
    if not os.path.exists(final_path):
        return {"status": "skipped", "reason": "file not found"}

    logger.info(f"Ingesting paid in/out activity from {final_path}")
    df = pd.read_csv(final_path, low_memory=False, encoding='utf-8-sig', skiprows=1)
    total_rows = len(df)

    existing_hashes = await get_existing_hashes(db, PaidInOutActivity, 'line_hash')
    inserted, skipped = 0, 0

    for idx, row in df.iterrows():
        try:
            date_val = parse_date(row.get('Date'))
            employee = parse_str(row.get('Employee'))
            terminal = parse_str(row.get('Terminal'))

            line_hash = generate_hash(date_val, employee, terminal)
            if line_hash in existing_hashes:
                skipped += 1
                continue

            record = PaidInOutActivity(
                line_hash=line_hash,
                date=date_val,
                cash_drawer_date=parse_date(row.get('Cash Drawer Date')),
                employee=employee,
                terminal=terminal,
                starting_cash=parse_float(row.get('Starting Cash')),
                day_end=parse_float(row.get('Day End')),
                daily_sales=parse_float(row.get('Daily Sales')),
                paid_in=parse_float(row.get('Paid In')),
                paid_out=parse_float(row.get('Paid Out')),
                cash_drop=parse_float(row.get('Cash Drop')),
                notes=parse_str(row.get('Notes')),
            )
            db.add(record)
            existing_hashes.add(line_hash)
            inserted += 1
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            await db.rollback()

    await db.commit()
    final_count = await db.scalar(select(func.count(PaidInOutActivity.id)))
    return {"table": "paidinout_activity", "csv_rows": total_rows, "inserted": inserted,
            "skipped_duplicate": skipped, "total_in_db": final_count}
