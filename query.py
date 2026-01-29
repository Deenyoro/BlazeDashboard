#!/usr/bin/env python3
"""
Query CLI for BlazeDB - Query your sales data from the command line.
"""
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "blazedb.sqlite"


def format_money(val):
    if val is None:
        return "$0.00"
    return f"${val:,.2f}"


def get_summary(conn):
    """Get database summary."""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("DATABASE SUMMARY")
    print("="*60)

    # Counts
    cursor.execute("SELECT count(*) FROM transactions")
    trans_count = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM members")
    member_count = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM employees")
    emp_count = cursor.fetchone()[0]

    print(f"Transactions: {trans_count:,}")
    print(f"Members:      {member_count:,}")
    print(f"Employees:    {emp_count:,}")

    # Date range
    cursor.execute("SELECT min(date), max(date) FROM transactions")
    min_date, max_date = cursor.fetchone()
    print(f"\nDate Range: {min_date[:10] if min_date else 'N/A'} to {max_date[:10] if max_date else 'N/A'}")

    # Financial summary
    cursor.execute("""
        SELECT
            sum(CASE WHEN trans_type='Sale' THEN gross_sales ELSE 0 END) as gross_sales,
            sum(CASE WHEN trans_type='Refund' THEN abs(gross_sales) ELSE 0 END) as refunds,
            sum(gross_sales) as net_revenue,
            sum(total_tax) as total_tax,
            sum(tips) as total_tips,
            sum(cogs) as total_cogs
        FROM transactions
    """)
    row = cursor.fetchone()
    gross_sales, refunds, net_revenue, total_tax, total_tips, total_cogs = row

    print(f"\n{'='*60}")
    print("FINANCIAL SUMMARY")
    print("="*60)
    print(f"Gross Sales:  {format_money(gross_sales)}")
    print(f"Refunds:      {format_money(refunds)}")
    print(f"Net Revenue:  {format_money(net_revenue)}")
    print(f"Total Tax:    {format_money(total_tax)}")
    print(f"Total Tips:   {format_money(total_tips)}")
    print(f"Total COGS:   {format_money(total_cogs)}")
    if net_revenue and total_cogs:
        margin = ((net_revenue - total_cogs) / net_revenue) * 100
        print(f"Gross Margin: {margin:.1f}%")


def get_by_type(conn):
    """Get breakdown by transaction type."""
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print("BY TRANSACTION TYPE")
    print("="*60)

    cursor.execute("""
        SELECT trans_type, count(*) as cnt, sum(gross_sales) as total
        FROM transactions
        GROUP BY trans_type
        ORDER BY cnt DESC
    """)

    print(f"{'Type':<20} {'Count':>10} {'Total':>15}")
    print("-"*45)
    for row in cursor.fetchall():
        print(f"{row[0] or 'Unknown':<20} {row[1]:>10,} {format_money(row[2]):>15}")


def get_by_payment(conn):
    """Get breakdown by payment type."""
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print("BY PAYMENT TYPE (Sales Only)")
    print("="*60)

    cursor.execute("""
        SELECT payment_type, count(*) as cnt, sum(total_due) as total
        FROM transactions
        WHERE trans_type = 'Sale'
        GROUP BY payment_type
        ORDER BY cnt DESC
    """)

    print(f"{'Payment Type':<20} {'Count':>10} {'Total':>15}")
    print("-"*45)
    for row in cursor.fetchall():
        print(f"{row[0] or 'Unknown':<20} {row[1]:>10,} {format_money(row[2]):>15}")


def get_by_queue(conn):
    """Get breakdown by queue type."""
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print("BY QUEUE TYPE (Sales Only)")
    print("="*60)

    cursor.execute("""
        SELECT queue_type, count(*) as cnt, sum(gross_sales) as total
        FROM transactions
        WHERE trans_type = 'Sale'
        GROUP BY queue_type
        ORDER BY total DESC
    """)

    print(f"{'Queue Type':<20} {'Count':>10} {'Total':>15}")
    print("-"*45)
    for row in cursor.fetchall():
        print(f"{row[0] or 'Unknown':<20} {row[1]:>10,} {format_money(row[2]):>15}")


def get_top_employees(conn, limit=10):
    """Get top employees by sales."""
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print(f"TOP {limit} EMPLOYEES BY SALES")
    print("="*60)

    cursor.execute("""
        SELECT sold_by_name, count(*) as cnt, sum(total_due) as total, avg(total_due) as avg
        FROM transactions
        WHERE trans_type = 'Sale' AND sold_by_name IS NOT NULL
        GROUP BY sold_by_name
        ORDER BY total DESC
        LIMIT ?
    """, (limit,))

    print(f"{'Employee':<25} {'Trans':>8} {'Total':>15} {'Avg':>12}")
    print("-"*60)
    for row in cursor.fetchall():
        print(f"{row[0]:<25} {row[1]:>8,} {format_money(row[2]):>15} {format_money(row[3]):>12}")


def get_top_customers(conn, limit=10):
    """Get top customers by spend."""
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print(f"TOP {limit} CUSTOMERS BY TOTAL SPEND")
    print("="*60)

    cursor.execute("""
        SELECT member_name, count(*) as cnt, sum(total_due) as total, avg(total_due) as avg
        FROM transactions
        WHERE trans_type = 'Sale' AND member_name IS NOT NULL
        GROUP BY member_id
        ORDER BY total DESC
        LIMIT ?
    """, (limit,))

    print(f"{'Customer':<30} {'Visits':>8} {'Total':>15} {'Avg':>12}")
    print("-"*65)
    for row in cursor.fetchall():
        name = row[0][:28] + '..' if len(row[0] or '') > 30 else (row[0] or 'Unknown')
        print(f"{name:<30} {row[1]:>8,} {format_money(row[2]):>15} {format_money(row[3]):>12}")


def get_daily_sales(conn, days=30):
    """Get daily sales for last N days."""
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print(f"DAILY SALES (Last {days} days with data)")
    print("="*60)

    cursor.execute("""
        SELECT date(date) as day,
               count(*) as cnt,
               sum(CASE WHEN trans_type='Sale' THEN gross_sales ELSE 0 END) as sales,
               sum(CASE WHEN trans_type='Refund' THEN abs(gross_sales) ELSE 0 END) as refunds
        FROM transactions
        GROUP BY date(date)
        ORDER BY day DESC
        LIMIT ?
    """, (days,))

    print(f"{'Date':<12} {'Trans':>8} {'Sales':>15} {'Refunds':>12}")
    print("-"*50)
    for row in cursor.fetchall():
        print(f"{row[0]:<12} {row[1]:>8,} {format_money(row[2]):>15} {format_money(row[3]):>12}")


def search_transactions(conn, search_term, limit=20):
    """Search transactions by member name, trans ID, or trans number."""
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print(f"SEARCH RESULTS: '{search_term}'")
    print("="*60)

    cursor.execute("""
        SELECT trans_no, date, member_name, trans_type, total_due, payment_type
        FROM transactions
        WHERE member_name LIKE ? OR blaze_trans_id LIKE ? OR trans_no LIKE ?
        ORDER BY date DESC
        LIMIT ?
    """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", limit))

    results = cursor.fetchall()
    if not results:
        print("No results found.")
        return

    print(f"{'Trans#':<8} {'Date':<12} {'Customer':<25} {'Type':<10} {'Total':>12} {'Payment':<10}")
    print("-"*80)
    for row in results:
        name = row[2][:23] + '..' if len(row[2] or '') > 25 else (row[2] or 'N/A')
        print(f"{row[0] or 'N/A':<8} {row[1][:10] if row[1] else 'N/A':<12} {name:<25} {row[3] or 'N/A':<10} {format_money(row[4]):>12} {row[5] or 'N/A':<10}")


def main():
    parser = argparse.ArgumentParser(description="Query BlazeDB sales data")
    parser.add_argument("--summary", action="store_true", help="Show database summary")
    parser.add_argument("--types", action="store_true", help="Breakdown by transaction type")
    parser.add_argument("--payments", action="store_true", help="Breakdown by payment type")
    parser.add_argument("--queues", action="store_true", help="Breakdown by queue type")
    parser.add_argument("--employees", type=int, nargs="?", const=10, help="Top employees (default: 10)")
    parser.add_argument("--customers", type=int, nargs="?", const=10, help="Top customers (default: 10)")
    parser.add_argument("--daily", type=int, nargs="?", const=30, help="Daily sales (default: 30 days)")
    parser.add_argument("--search", type=str, help="Search by customer name or transaction ID")
    parser.add_argument("--all", action="store_true", help="Show all reports")

    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run 'python3 ingest_simple.py' first to create the database.")
        return

    conn = sqlite3.connect(str(DB_PATH))

    # If no arguments, show summary
    if not any([args.summary, args.types, args.payments, args.queues,
                args.employees, args.customers, args.daily, args.search, args.all]):
        args.summary = True

    if args.all or args.summary:
        get_summary(conn)

    if args.all or args.types:
        get_by_type(conn)

    if args.all or args.payments:
        get_by_payment(conn)

    if args.all or args.queues:
        get_by_queue(conn)

    if args.all or args.employees:
        get_top_employees(conn, args.employees or 10)

    if args.all or args.customers:
        get_top_customers(conn, args.customers or 10)

    if args.all or args.daily:
        get_daily_sales(conn, args.daily or 30)

    if args.search:
        search_transactions(conn, args.search)

    conn.close()
    print()


if __name__ == "__main__":
    main()
