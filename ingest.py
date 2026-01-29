#!/usr/bin/env python3
"""
Standalone script to ingest Blaze CSV data into SQLite database.
"""
import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Add the API app to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey, Index, select
import uuid


# Database setup
DB_PATH = Path(__file__).parent / "blazedb.sqlite"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"


class Base(DeclarativeBase):
    pass


def generate_uuid():
    return str(uuid.uuid4())


class Member(Base):
    __tablename__ = "members"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    blaze_member_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    member_group = Column(String(100), nullable=True)
    consumer_tax_type = Column(String(50), nullable=True)


class Employee(Base):
    __tablename__ = "employees"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), unique=True, nullable=False, index=True)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    blaze_trans_id = Column(String(50), unique=True, nullable=False, index=True)
    trans_no = Column(String(50), nullable=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    created_date = Column(DateTime, nullable=True)
    prepared_date = Column(DateTime, nullable=True)
    packed_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)
    shop = Column(String(255), nullable=True, index=True)
    company = Column(String(500), nullable=True)
    terminal = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    delivery_city = Column(String(100), nullable=True, index=True)
    trans_type = Column(String(50), nullable=True, index=True)
    trans_status = Column(String(50), nullable=True, index=True)
    queue_type = Column(String(50), nullable=True, index=True)
    order_source = Column(String(100), nullable=True)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=True)
    retail_value = Column(Float, default=0.0)
    gross_sales = Column(Float, default=0.0)
    net_sales = Column(Float, default=0.0)
    net_sales_wo_fees = Column(Float, default=0.0)
    delivery_fees = Column(Float, default=0.0)
    pre_tax_discounts = Column(Float, default=0.0)
    after_tax_discount = Column(Float, default=0.0)
    product_promotions = Column(Text, nullable=True)
    cart_promotions = Column(Text, nullable=True)
    discount_notes = Column(Text, nullable=True)
    pre_al_excise_tax = Column(Float, default=0.0)
    pre_nal_excise_tax = Column(Float, default=0.0)
    pre_city_tax = Column(Float, default=0.0)
    pre_county_tax = Column(Float, default=0.0)
    pre_state_tax = Column(Float, default=0.0)
    pre_fed_tax = Column(Float, default=0.0)
    post_al_excise_tax = Column(Float, default=0.0)
    post_nal_excise_tax = Column(Float, default=0.0)
    city_tax = Column(Float, default=0.0)
    county_tax = Column(Float, default=0.0)
    state_tax = Column(Float, default=0.0)
    federal_tax = Column(Float, default=0.0)
    delivery_fee_excise_tax = Column(Float, default=0.0)
    city_delivery_fee_tax = Column(Float, default=0.0)
    county_delivery_fee_tax = Column(Float, default=0.0)
    state_delivery_fee_tax = Column(Float, default=0.0)
    fed_delivery_fee_tax = Column(Float, default=0.0)
    total_tax = Column(Float, default=0.0)
    rounded_amount = Column(Float, default=0.0)
    adjustments = Column(Float, default=0.0)
    payment_fee = Column(Float, default=0.0)
    total_due = Column(Float, default=0.0)
    surcharge_fee_tax = Column(Float, default=0.0)
    untaxed_fee = Column(Float, default=0.0)
    tips = Column(Float, default=0.0)
    blazepay_tips = Column(Float, default=0.0)
    cogs = Column(Float, default=0.0)
    payment_type = Column(String(50), nullable=True, index=True)
    blazepay_id = Column(String(100), nullable=True)
    payment_tendered = Column(Float, default=0.0)
    cash_change = Column(Float, default=0.0)
    cashless_atm_change = Column(Float, default=0.0)
    change_due = Column(Float, default=0.0)
    sold_by_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    sold_by_name = Column(String(255), nullable=True)
    created_by_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    created_by_name = Column(String(255), nullable=True)
    prepared_by = Column(String(255), nullable=True)
    packed_by = Column(String(255), nullable=True)
    marketing_source = Column(String(255), nullable=True)
    order_tags = Column(Text, nullable=True)
    loyalty_points_spent = Column(Float, default=0.0)
    loyalty_points_earned = Column(Float, default=0.0)
    compliance_system = Column(String(50), nullable=True)
    compliance_order_id = Column(String(100), nullable=True)
    compliance_delivery_id = Column(String(100), nullable=True)
    compliance_delivery_ledger_id = Column(String(100), nullable=True)
    compliance_delivery_submit_status = Column(String(100), nullable=True)
    submission_error = Column(Text, nullable=True)

    __table_args__ = (
        Index('ix_transactions_date_shop', 'date', 'shop'),
        Index('ix_transactions_date_type', 'date', 'trans_type'),
        Index('ix_transactions_payment_date', 'payment_type', 'date'),
    )


def parse_datetime(val):
    if pd.isna(val) or val == "" or val is None:
        return None
    try:
        if isinstance(val, datetime):
            return val
        if "1969-12-31" in str(val):
            return None
        return pd.to_datetime(val)
    except Exception:
        return None


def parse_float(val):
    if pd.isna(val) or val == "" or val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def parse_str(val):
    if pd.isna(val) or val == "" or val is None:
        return None
    return str(val).strip()


async def main():
    csv_path = Path(__file__).parent / "total_sales.csv"

    if not csv_path.exists():
        print(f"ERROR: CSV file not found at {csv_path}")
        return

    print(f"Creating database at {DB_PATH}")

    engine = create_async_engine(DATABASE_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print(f"Reading CSV from {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    total_rows = len(df)
    print(f"Found {total_rows} rows to process")

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        member_cache = {}
        employee_cache = {}
        inserted = 0
        skipped = 0
        errors = 0

        for idx, row in df.iterrows():
            try:
                blaze_trans_id = parse_str(row.get("Trans ID"))
                if not blaze_trans_id:
                    skipped += 1
                    continue

                # Check if exists
                existing = await db.execute(
                    select(Transaction).where(Transaction.blaze_trans_id == blaze_trans_id)
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

                # Handle member
                member_id_str = parse_str(row.get("Member ID"))
                member_db_id = None
                if member_id_str:
                    if member_id_str not in member_cache:
                        existing_member = await db.execute(
                            select(Member).where(Member.blaze_member_id == member_id_str)
                        )
                        member = existing_member.scalar_one_or_none()
                        if not member:
                            member = Member(
                                blaze_member_id=member_id_str,
                                name=parse_str(row.get("Member")),
                                member_group=parse_str(row.get("Member Group")),
                                consumer_tax_type=parse_str(row.get("Consumer Tax Type")),
                            )
                            db.add(member)
                            await db.flush()
                        member_cache[member_id_str] = member.id
                    member_db_id = member_cache[member_id_str]

                # Handle employees
                sold_by_name = parse_str(row.get("Sold By"))
                sold_by_id = None
                if sold_by_name:
                    if sold_by_name not in employee_cache:
                        existing_emp = await db.execute(
                            select(Employee).where(Employee.name == sold_by_name)
                        )
                        emp = existing_emp.scalar_one_or_none()
                        if not emp:
                            emp = Employee(name=sold_by_name)
                            db.add(emp)
                            await db.flush()
                        employee_cache[sold_by_name] = emp.id
                    sold_by_id = employee_cache[sold_by_name]

                created_by_name = parse_str(row.get("Created By"))
                created_by_id = None
                if created_by_name:
                    if created_by_name not in employee_cache:
                        existing_emp = await db.execute(
                            select(Employee).where(Employee.name == created_by_name)
                        )
                        emp = existing_emp.scalar_one_or_none()
                        if not emp:
                            emp = Employee(name=created_by_name)
                            db.add(emp)
                            await db.flush()
                        employee_cache[created_by_name] = emp.id
                    created_by_id = employee_cache[created_by_name]

                transaction = Transaction(
                    blaze_trans_id=blaze_trans_id,
                    trans_no=parse_str(row.get("Trans No")),
                    date=parse_datetime(row.get("Date")),
                    created_date=parse_datetime(row.get("Created Date")),
                    prepared_date=parse_datetime(row.get("Prepared Date")),
                    packed_date=parse_datetime(row.get("Packed Date")),
                    start_date=parse_datetime(row.get("Start Date")),
                    end_date=parse_datetime(row.get("End Date")),
                    delivery_date=parse_datetime(row.get("Delivery Date")),
                    shop=parse_str(row.get("Shop")),
                    company=parse_str(row.get("Company")),
                    terminal=parse_str(row.get("Terminal")),
                    region=parse_str(row.get("Region")),
                    delivery_city=parse_str(row.get("Delivery City")),
                    trans_type=parse_str(row.get("Trans Type")),
                    trans_status=parse_str(row.get("Trans Status")),
                    queue_type=parse_str(row.get("Queue Type")),
                    order_source=parse_str(row.get("Order Source")),
                    member_id=member_db_id,
                    retail_value=parse_float(row.get("Retail Value of Sales")),
                    gross_sales=parse_float(row.get("Gross Sales")),
                    net_sales=parse_float(row.get("Net Sales")),
                    net_sales_wo_fees=parse_float(row.get("Net Sales w/o Fees")),
                    delivery_fees=parse_float(row.get("Delivery Fees")),
                    pre_tax_discounts=parse_float(row.get("Pre Tax Discounts")),
                    after_tax_discount=parse_float(row.get("After Tax Discount")),
                    product_promotions=parse_str(row.get("Product Promotions")),
                    cart_promotions=parse_str(row.get("Cart Promotions")),
                    discount_notes=parse_str(row.get("Discount Notes")),
                    pre_al_excise_tax=parse_float(row.get("Pre AL Excise Tax")),
                    pre_nal_excise_tax=parse_float(row.get("Pre NAL Excise Tax")),
                    pre_city_tax=parse_float(row.get("Pre City Tax")),
                    pre_county_tax=parse_float(row.get("Pre County Tax")),
                    pre_state_tax=parse_float(row.get("Pre State Tax")),
                    pre_fed_tax=parse_float(row.get("Pre Fed Tax")),
                    post_al_excise_tax=parse_float(row.get("Post AL Excise Tax")),
                    post_nal_excise_tax=parse_float(row.get("Post NAL Excise Tax")),
                    city_tax=parse_float(row.get("City Tax")),
                    county_tax=parse_float(row.get("County Tax")),
                    state_tax=parse_float(row.get("State Tax")),
                    federal_tax=parse_float(row.get("Federal Tax")),
                    delivery_fee_excise_tax=parse_float(row.get("Delivery Fee Excise Tax")),
                    city_delivery_fee_tax=parse_float(row.get("City Delivery Fee Tax")),
                    county_delivery_fee_tax=parse_float(row.get("County Delivery Fee Tax")),
                    state_delivery_fee_tax=parse_float(row.get("State Delivery Fee Tax")),
                    fed_delivery_fee_tax=parse_float(row.get("Fed Delivery Fee Tax")),
                    total_tax=parse_float(row.get("Total Tax")),
                    rounded_amount=parse_float(row.get("Rounded Amount")),
                    adjustments=parse_float(row.get("Adjustments")),
                    payment_fee=parse_float(row.get("Payment Fee")),
                    total_due=parse_float(row.get("Total Due")),
                    surcharge_fee_tax=parse_float(row.get("Surcharge Fee Tax")),
                    untaxed_fee=parse_float(row.get("Untaxed Fee")),
                    tips=parse_float(row.get("Tips")),
                    blazepay_tips=parse_float(row.get("BLAZEPAY Tips")),
                    cogs=parse_float(row.get("COGS")),
                    payment_type=parse_str(row.get("Payment Type")),
                    blazepay_id=parse_str(row.get("BLAZEPAY ID")),
                    payment_tendered=parse_float(row.get("Payment Tendered")),
                    cash_change=parse_float(row.get("Cash Change")),
                    cashless_atm_change=parse_float(row.get("Cashless ATM Change")),
                    change_due=parse_float(row.get("Change Due")),
                    sold_by_id=sold_by_id,
                    sold_by_name=sold_by_name,
                    created_by_id=created_by_id,
                    created_by_name=created_by_name,
                    prepared_by=parse_str(row.get("Prepared By")),
                    packed_by=parse_str(row.get("Packed By")),
                    marketing_source=parse_str(row.get("Marketing Source")),
                    order_tags=parse_str(row.get("Order Tags")),
                    loyalty_points_spent=parse_float(row.get("Loyalty Points Spent")),
                    loyalty_points_earned=parse_float(row.get("Loyalty Points Earned")),
                    compliance_system=parse_str(row.get("Compliance System")),
                    compliance_order_id=parse_str(row.get("Compliance Order ID")),
                    compliance_delivery_id=parse_str(row.get("Compliance Delivery ID")),
                    compliance_delivery_ledger_id=parse_str(row.get("Compliance Delivery Ledger ID")),
                    compliance_delivery_submit_status=parse_str(row.get("Compliance Delivery Submit Status")),
                    submission_error=parse_str(row.get("Submission Error")),
                )

                db.add(transaction)
                inserted += 1

                if inserted % 500 == 0:
                    await db.commit()
                    print(f"Progress: {inserted}/{total_rows} inserted ({(inserted/total_rows)*100:.1f}%)")

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"Error on row {idx}: {e}")
                continue

        await db.commit()

    print(f"\n{'='*50}")
    print(f"INGESTION COMPLETE")
    print(f"{'='*50}")
    print(f"Total rows: {total_rows}")
    print(f"Inserted: {inserted}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")
    print(f"Members created: {len(member_cache)}")
    print(f"Employees created: {len(employee_cache)}")
    print(f"\nDatabase saved to: {DB_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
