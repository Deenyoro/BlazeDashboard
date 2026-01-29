#!/usr/bin/env python3
"""
Simple standalone script to ingest Blaze CSV into SQLite using only stdlib.
"""
import csv
import sqlite3
import uuid
from pathlib import Path


DB_PATH = Path(__file__).parent / "blazedb.sqlite"
CSV_PATH = Path(__file__).parent / "total_sales.csv"


def create_tables(conn):
    """Create all tables."""
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members (
        id TEXT PRIMARY KEY,
        blaze_member_id TEXT UNIQUE NOT NULL,
        name TEXT,
        member_group TEXT,
        consumer_tax_type TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        blaze_trans_id TEXT UNIQUE NOT NULL,
        trans_no TEXT,
        date TEXT,
        created_date TEXT,
        prepared_date TEXT,
        packed_date TEXT,
        start_date TEXT,
        end_date TEXT,
        delivery_date TEXT,
        shop TEXT,
        company TEXT,
        terminal TEXT,
        region TEXT,
        delivery_city TEXT,
        trans_type TEXT,
        trans_status TEXT,
        queue_type TEXT,
        order_source TEXT,
        member_id TEXT,
        member_name TEXT,
        retail_value REAL DEFAULT 0.0,
        gross_sales REAL DEFAULT 0.0,
        net_sales REAL DEFAULT 0.0,
        net_sales_wo_fees REAL DEFAULT 0.0,
        delivery_fees REAL DEFAULT 0.0,
        pre_tax_discounts REAL DEFAULT 0.0,
        after_tax_discount REAL DEFAULT 0.0,
        product_promotions TEXT,
        cart_promotions TEXT,
        discount_notes TEXT,
        pre_al_excise_tax REAL DEFAULT 0.0,
        pre_nal_excise_tax REAL DEFAULT 0.0,
        pre_city_tax REAL DEFAULT 0.0,
        pre_county_tax REAL DEFAULT 0.0,
        pre_state_tax REAL DEFAULT 0.0,
        pre_fed_tax REAL DEFAULT 0.0,
        post_al_excise_tax REAL DEFAULT 0.0,
        post_nal_excise_tax REAL DEFAULT 0.0,
        city_tax REAL DEFAULT 0.0,
        county_tax REAL DEFAULT 0.0,
        state_tax REAL DEFAULT 0.0,
        federal_tax REAL DEFAULT 0.0,
        delivery_fee_excise_tax REAL DEFAULT 0.0,
        city_delivery_fee_tax REAL DEFAULT 0.0,
        county_delivery_fee_tax REAL DEFAULT 0.0,
        state_delivery_fee_tax REAL DEFAULT 0.0,
        fed_delivery_fee_tax REAL DEFAULT 0.0,
        total_tax REAL DEFAULT 0.0,
        rounded_amount REAL DEFAULT 0.0,
        adjustments REAL DEFAULT 0.0,
        payment_fee REAL DEFAULT 0.0,
        total_due REAL DEFAULT 0.0,
        surcharge_fee_tax REAL DEFAULT 0.0,
        untaxed_fee REAL DEFAULT 0.0,
        tips REAL DEFAULT 0.0,
        blazepay_tips REAL DEFAULT 0.0,
        cogs REAL DEFAULT 0.0,
        payment_type TEXT,
        blazepay_id TEXT,
        payment_tendered REAL DEFAULT 0.0,
        cash_change REAL DEFAULT 0.0,
        cashless_atm_change REAL DEFAULT 0.0,
        change_due REAL DEFAULT 0.0,
        sold_by_id TEXT,
        sold_by_name TEXT,
        created_by_id TEXT,
        created_by_name TEXT,
        prepared_by TEXT,
        packed_by TEXT,
        marketing_source TEXT,
        order_tags TEXT,
        loyalty_points_spent REAL DEFAULT 0.0,
        loyalty_points_earned REAL DEFAULT 0.0,
        compliance_system TEXT,
        compliance_order_id TEXT,
        compliance_delivery_id TEXT,
        compliance_delivery_ledger_id TEXT,
        compliance_delivery_submit_status TEXT,
        submission_error TEXT,
        FOREIGN KEY (member_id) REFERENCES members(id),
        FOREIGN KEY (sold_by_id) REFERENCES employees(id),
        FOREIGN KEY (created_by_id) REFERENCES employees(id)
    )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_transactions_date ON transactions(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_transactions_trans_type ON transactions(trans_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_transactions_queue_type ON transactions(queue_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_transactions_payment_type ON transactions(payment_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_transactions_shop ON transactions(shop)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_transactions_blaze_id ON transactions(blaze_trans_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_members_blaze_id ON members(blaze_member_id)")

    conn.commit()


def parse_float(val):
    if not val or val.strip() == "":
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def parse_str(val):
    if not val or val.strip() == "":
        return None
    return val.strip()


def parse_datetime(val):
    if not val or val.strip() == "" or "1969-12-31" in val:
        return None
    return val.strip()


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: CSV file not found at {CSV_PATH}")
        return

    print(f"Database: {DB_PATH}")
    print(f"CSV: {CSV_PATH}")

    # Remove existing DB for fresh start
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Removed existing database")

    conn = sqlite3.connect(str(DB_PATH))
    create_tables(conn)
    cursor = conn.cursor()

    member_cache = {}
    employee_cache = {}
    inserted = 0
    skipped = 0
    errors = 0

    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total_rows = sum(1 for _ in open(CSV_PATH)) - 1  # minus header
        f.seek(0)
        reader = csv.DictReader(f)

        print(f"Processing {total_rows} rows...")

        for idx, row in enumerate(reader):
            try:
                blaze_trans_id = parse_str(row.get("Trans ID"))
                if not blaze_trans_id:
                    skipped += 1
                    continue

                # Check if already exists
                cursor.execute("SELECT id FROM transactions WHERE blaze_trans_id = ?", (blaze_trans_id,))
                if cursor.fetchone():
                    skipped += 1
                    continue

                # Handle member
                member_id_str = parse_str(row.get("Member ID"))
                member_db_id = None
                member_name = parse_str(row.get("Member"))
                if member_id_str:
                    if member_id_str not in member_cache:
                        cursor.execute("SELECT id FROM members WHERE blaze_member_id = ?", (member_id_str,))
                        existing = cursor.fetchone()
                        if existing:
                            member_cache[member_id_str] = existing[0]
                        else:
                            new_id = str(uuid.uuid4())
                            cursor.execute(
                                "INSERT INTO members (id, blaze_member_id, name, member_group, consumer_tax_type) VALUES (?, ?, ?, ?, ?)",
                                (new_id, member_id_str, member_name,
                                 parse_str(row.get("Member Group")), parse_str(row.get("Consumer Tax Type")))
                            )
                            member_cache[member_id_str] = new_id
                    member_db_id = member_cache[member_id_str]

                # Handle sold by employee
                sold_by_name = parse_str(row.get("Sold By"))
                sold_by_id = None
                if sold_by_name:
                    if sold_by_name not in employee_cache:
                        cursor.execute("SELECT id FROM employees WHERE name = ?", (sold_by_name,))
                        existing = cursor.fetchone()
                        if existing:
                            employee_cache[sold_by_name] = existing[0]
                        else:
                            new_id = str(uuid.uuid4())
                            cursor.execute("INSERT INTO employees (id, name) VALUES (?, ?)", (new_id, sold_by_name))
                            employee_cache[sold_by_name] = new_id
                    sold_by_id = employee_cache[sold_by_name]

                # Handle created by employee
                created_by_name = parse_str(row.get("Created By"))
                created_by_id = None
                if created_by_name:
                    if created_by_name not in employee_cache:
                        cursor.execute("SELECT id FROM employees WHERE name = ?", (created_by_name,))
                        existing = cursor.fetchone()
                        if existing:
                            employee_cache[created_by_name] = existing[0]
                        else:
                            new_id = str(uuid.uuid4())
                            cursor.execute("INSERT INTO employees (id, name) VALUES (?, ?)", (new_id, created_by_name))
                            employee_cache[created_by_name] = new_id
                    created_by_id = employee_cache[created_by_name]

                # Insert transaction
                trans_id = str(uuid.uuid4())

                values = (
                    trans_id,
                    blaze_trans_id,
                    parse_str(row.get("Trans No")),
                    parse_datetime(row.get("Date")),
                    parse_datetime(row.get("Created Date")),
                    parse_datetime(row.get("Prepared Date")),
                    parse_datetime(row.get("Packed Date")),
                    parse_datetime(row.get("Start Date")),
                    parse_datetime(row.get("End Date")),
                    parse_datetime(row.get("Delivery Date")),
                    parse_str(row.get("Shop")),
                    parse_str(row.get("Company")),
                    parse_str(row.get("Terminal")),
                    parse_str(row.get("Region")),
                    parse_str(row.get("Delivery City")),
                    parse_str(row.get("Trans Type")),
                    parse_str(row.get("Trans Status")),
                    parse_str(row.get("Queue Type")),
                    parse_str(row.get("Order Source")),
                    member_db_id,
                    member_name,
                    parse_float(row.get("Retail Value of Sales")),
                    parse_float(row.get("Gross Sales")),
                    parse_float(row.get("Net Sales")),
                    parse_float(row.get("Net Sales w/o Fees")),
                    parse_float(row.get("Delivery Fees")),
                    parse_float(row.get("Pre Tax Discounts")),
                    parse_float(row.get("After Tax Discount")),
                    parse_str(row.get("Product Promotions")),
                    parse_str(row.get("Cart Promotions")),
                    parse_str(row.get("Discount Notes")),
                    parse_float(row.get("Pre AL Excise Tax")),
                    parse_float(row.get("Pre NAL Excise Tax")),
                    parse_float(row.get("Pre City Tax")),
                    parse_float(row.get("Pre County Tax")),
                    parse_float(row.get("Pre State Tax")),
                    parse_float(row.get("Pre Fed Tax")),
                    parse_float(row.get("Post AL Excise Tax")),
                    parse_float(row.get("Post NAL Excise Tax")),
                    parse_float(row.get("City Tax")),
                    parse_float(row.get("County Tax")),
                    parse_float(row.get("State Tax")),
                    parse_float(row.get("Federal Tax")),
                    parse_float(row.get("Delivery Fee Excise Tax")),
                    parse_float(row.get("City Delivery Fee Tax")),
                    parse_float(row.get("County Delivery Fee Tax")),
                    parse_float(row.get("State Delivery Fee Tax")),
                    parse_float(row.get("Fed Delivery Fee Tax")),
                    parse_float(row.get("Total Tax")),
                    parse_float(row.get("Rounded Amount")),
                    parse_float(row.get("Adjustments")),
                    parse_float(row.get("Payment Fee")),
                    parse_float(row.get("Total Due")),
                    parse_float(row.get("Surcharge Fee Tax")),
                    parse_float(row.get("Untaxed Fee")),
                    parse_float(row.get("Tips")),
                    parse_float(row.get("BLAZEPAY Tips")),
                    parse_float(row.get("COGS")),
                    parse_str(row.get("Payment Type")),
                    parse_str(row.get("BLAZEPAY ID")),
                    parse_float(row.get("Payment Tendered")),
                    parse_float(row.get("Cash Change")),
                    parse_float(row.get("Cashless ATM Change")),
                    parse_float(row.get("Change Due")),
                    sold_by_id,
                    sold_by_name,
                    created_by_id,
                    created_by_name,
                    parse_str(row.get("Prepared By")),
                    parse_str(row.get("Packed By")),
                    parse_str(row.get("Marketing Source")),
                    parse_str(row.get("Order Tags")),
                    parse_float(row.get("Loyalty Points Spent")),
                    parse_float(row.get("Loyalty Points Earned")),
                    parse_str(row.get("Compliance System")),
                    parse_str(row.get("Compliance Order ID")),
                    parse_str(row.get("Compliance Delivery ID")),
                    parse_str(row.get("Compliance Delivery Ledger ID")),
                    parse_str(row.get("Compliance Delivery Submit Status")),
                    parse_str(row.get("Submission Error")),
                )

                placeholders = ",".join(["?"] * len(values))
                cursor.execute(f"""
                INSERT INTO transactions (
                    id, blaze_trans_id, trans_no, date, created_date, prepared_date, packed_date,
                    start_date, end_date, delivery_date, shop, company, terminal, region, delivery_city,
                    trans_type, trans_status, queue_type, order_source, member_id, member_name,
                    retail_value, gross_sales, net_sales, net_sales_wo_fees, delivery_fees,
                    pre_tax_discounts, after_tax_discount, product_promotions, cart_promotions, discount_notes,
                    pre_al_excise_tax, pre_nal_excise_tax, pre_city_tax, pre_county_tax, pre_state_tax, pre_fed_tax,
                    post_al_excise_tax, post_nal_excise_tax, city_tax, county_tax, state_tax, federal_tax,
                    delivery_fee_excise_tax, city_delivery_fee_tax, county_delivery_fee_tax, state_delivery_fee_tax, fed_delivery_fee_tax,
                    total_tax, rounded_amount, adjustments, payment_fee, total_due, surcharge_fee_tax, untaxed_fee,
                    tips, blazepay_tips, cogs, payment_type, blazepay_id,
                    payment_tendered, cash_change, cashless_atm_change, change_due,
                    sold_by_id, sold_by_name, created_by_id, created_by_name, prepared_by, packed_by,
                    marketing_source, order_tags, loyalty_points_spent, loyalty_points_earned,
                    compliance_system, compliance_order_id, compliance_delivery_id, compliance_delivery_ledger_id,
                    compliance_delivery_submit_status, submission_error
                ) VALUES ({placeholders})
                """, values)

                inserted += 1

                if inserted % 2000 == 0:
                    conn.commit()
                    pct = (inserted / total_rows) * 100
                    print(f"Progress: {inserted:,}/{total_rows:,} ({pct:.1f}%)")

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"Error on row {idx}: {e}")
                continue

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"INGESTION COMPLETE")
    print(f"{'='*60}")
    print(f"Total rows in CSV:    {total_rows:,}")
    print(f"Inserted:             {inserted:,}")
    print(f"Skipped (duplicates): {skipped:,}")
    print(f"Errors:               {errors:,}")
    print(f"Members created:      {len(member_cache):,}")
    print(f"Employees created:    {len(employee_cache):,}")
    print(f"\nDatabase saved to: {DB_PATH}")
    print(f"Database size: {DB_PATH.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
