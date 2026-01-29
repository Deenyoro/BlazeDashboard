import os
import csv
import sqlite3
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="BlazeDB API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.environ.get("DB_PATH", "/data/blazedb.sqlite")
CSV_PATH = os.environ.get("CSV_PATH", "/data/total_sales.csv")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# Pydantic models
class Transaction(BaseModel):
    id: int
    blaze_trans_id: Optional[str]
    trans_no: Optional[str]
    date: Optional[str]
    shop: Optional[str]
    company: Optional[str]
    trans_type: Optional[str]
    trans_status: Optional[str]
    queue_type: Optional[str]
    order_source: Optional[str]
    gross_sales: float
    net_sales: float
    total_tax: float
    total_due: float
    tips: float
    cogs: float
    pre_tax_discounts: float
    after_tax_discount: float
    payment_type: Optional[str]
    payment_tendered: float
    sold_by_name: Optional[str]
    created_by_name: Optional[str]
    terminal: Optional[str]
    region: Optional[str]
    delivery_city: Optional[str]
    loyalty_points_spent: float
    loyalty_points_earned: float
    compliance_system: Optional[str]
    compliance_order_id: Optional[str]


class TransactionListResponse(BaseModel):
    transactions: list[dict]
    total: int
    skip: int
    limit: int


class TransactionStats(BaseModel):
    total_transactions: int
    total_sales: float
    total_refunds: float
    net_revenue: float
    total_tax_collected: float
    total_tips: float
    total_discounts: float
    average_transaction: float
    total_cogs: float
    gross_margin: float


class IngestionStatus(BaseModel):
    transactions: int
    members: int
    employees: int
    date_range: dict
    by_type: dict


# API Routes
@app.get("/api/v1/transactions", response_model=TransactionListResponse)
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    trans_type: Optional[str] = None,
    queue_type: Optional[str] = None,
    payment_type: Optional[str] = None,
    employee: Optional[str] = None,
    search: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
):
    with get_db() as conn:
        where_clauses = []
        params = []

        if start_date:
            where_clauses.append("date >= ?")
            params.append(start_date)
        if end_date:
            where_clauses.append("date <= ?")
            params.append(end_date + " 23:59:59")
        if trans_type:
            where_clauses.append("trans_type = ?")
            params.append(trans_type)
        if queue_type:
            where_clauses.append("queue_type = ?")
            params.append(queue_type)
        if payment_type:
            where_clauses.append("payment_type = ?")
            params.append(payment_type)
        if employee:
            where_clauses.append("sold_by_name LIKE ?")
            params.append(f"%{employee}%")
        if search:
            where_clauses.append(
                "(trans_no LIKE ? OR sold_by_name LIKE ? OR created_by_name LIKE ?)"
            )
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        if min_amount is not None:
            where_clauses.append("total_due >= ?")
            params.append(min_amount)
        if max_amount is not None:
            where_clauses.append("total_due <= ?")
            params.append(max_amount)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count
        count_sql = f"SELECT COUNT(*) FROM transactions WHERE {where_sql}"
        total = conn.execute(count_sql, params).fetchone()[0]

        # Get transactions
        query_sql = f"""
            SELECT * FROM transactions
            WHERE {where_sql}
            ORDER BY date DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(query_sql, params + [limit, skip]).fetchall()

        transactions = [dict(row) for row in rows]

        return TransactionListResponse(
            transactions=transactions, total=total, skip=skip, limit=limit
        )


@app.get("/api/v1/transactions/stats", response_model=TransactionStats)
def get_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    with get_db() as conn:
        where_clauses = []
        params = []

        if start_date:
            where_clauses.append("date >= ?")
            params.append(start_date)
        if end_date:
            where_clauses.append("date <= ?")
            params.append(end_date + " 23:59:59")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
            SELECT
                COUNT(*) as total_transactions,
                COALESCE(SUM(CASE WHEN trans_type != 'Refund' THEN gross_sales ELSE 0 END), 0) as total_sales,
                COALESCE(SUM(CASE WHEN trans_type = 'Refund' THEN ABS(total_due) ELSE 0 END), 0) as total_refunds,
                COALESCE(SUM(total_due), 0) as net_revenue,
                COALESCE(SUM(total_tax), 0) as total_tax_collected,
                COALESCE(SUM(tips), 0) as total_tips,
                COALESCE(SUM(pre_tax_discounts + after_tax_discount), 0) as total_discounts,
                COALESCE(AVG(CASE WHEN trans_type != 'Refund' THEN total_due ELSE NULL END), 0) as average_transaction,
                COALESCE(SUM(cogs), 0) as total_cogs
            FROM transactions
            WHERE {where_sql}
        """

        row = conn.execute(query, params).fetchone()

        net_revenue = row["net_revenue"] or 0
        total_cogs = row["total_cogs"] or 0
        gross_margin = (
            ((net_revenue - total_cogs) / net_revenue * 100) if net_revenue > 0 else 0
        )

        return TransactionStats(
            total_transactions=row["total_transactions"],
            total_sales=row["total_sales"],
            total_refunds=row["total_refunds"],
            net_revenue=net_revenue,
            total_tax_collected=row["total_tax_collected"],
            total_tips=row["total_tips"],
            total_discounts=row["total_discounts"],
            average_transaction=row["average_transaction"],
            total_cogs=total_cogs,
            gross_margin=round(gross_margin, 2),
        )


@app.get("/api/v1/transactions/overview")
def get_overview(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    with get_db() as conn:
        where_clauses = []
        params = []

        if start_date:
            where_clauses.append("date >= ?")
            params.append(start_date)
        if end_date:
            where_clauses.append("date <= ?")
            params.append(end_date + " 23:59:59")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get stats
        stats_query = f"""
            SELECT
                COUNT(*) as total_transactions,
                COALESCE(SUM(CASE WHEN trans_type != 'Refund' THEN gross_sales ELSE 0 END), 0) as total_sales,
                COALESCE(SUM(CASE WHEN trans_type = 'Refund' THEN ABS(total_due) ELSE 0 END), 0) as total_refunds,
                COALESCE(SUM(total_due), 0) as net_revenue,
                COALESCE(SUM(total_tax), 0) as total_tax_collected,
                COALESCE(SUM(tips), 0) as total_tips,
                COALESCE(SUM(pre_tax_discounts + after_tax_discount), 0) as total_discounts,
                COALESCE(AVG(CASE WHEN trans_type != 'Refund' THEN total_due ELSE NULL END), 0) as average_transaction,
                COALESCE(SUM(cogs), 0) as total_cogs
            FROM transactions
            WHERE {where_sql}
        """
        stats_row = conn.execute(stats_query, params).fetchone()

        net_revenue = stats_row["net_revenue"] or 0
        total_cogs = stats_row["total_cogs"] or 0
        gross_margin = (
            ((net_revenue - total_cogs) / net_revenue * 100) if net_revenue > 0 else 0
        )

        stats = {
            "total_transactions": stats_row["total_transactions"],
            "total_sales": stats_row["total_sales"],
            "total_refunds": stats_row["total_refunds"],
            "net_revenue": net_revenue,
            "total_tax_collected": stats_row["total_tax_collected"],
            "total_tips": stats_row["total_tips"],
            "total_discounts": stats_row["total_discounts"],
            "average_transaction": stats_row["average_transaction"],
            "total_cogs": total_cogs,
            "gross_margin": round(gross_margin, 2),
        }

        # Daily breakdown
        daily_query = f"""
            SELECT
                DATE(date) as date,
                COUNT(*) as transaction_count,
                COALESCE(SUM(gross_sales), 0) as gross_sales,
                COALESCE(SUM(net_sales), 0) as net_sales,
                COALESCE(SUM(total_tax), 0) as total_tax,
                COALESCE(SUM(tips), 0) as tips,
                COALESCE(SUM(CASE WHEN trans_type = 'Refund' THEN ABS(total_due) ELSE 0 END), 0) as refunds
            FROM transactions
            WHERE {where_sql}
            GROUP BY DATE(date)
            ORDER BY date
        """
        daily_rows = conn.execute(daily_query, params).fetchall()
        daily_breakdown = [dict(row) for row in daily_rows]

        # By payment type
        payment_query = f"""
            SELECT
                payment_type,
                COUNT(*) as count,
                COALESCE(SUM(total_due), 0) as total
            FROM transactions
            WHERE {where_sql} AND payment_type IS NOT NULL
            GROUP BY payment_type
        """
        payment_rows = conn.execute(payment_query, params).fetchall()
        by_payment_type = {
            row["payment_type"]: {"count": row["count"], "total": row["total"]}
            for row in payment_rows
        }

        # By queue type
        queue_query = f"""
            SELECT
                queue_type,
                COUNT(*) as count,
                COALESCE(SUM(total_due), 0) as total
            FROM transactions
            WHERE {where_sql} AND queue_type IS NOT NULL
            GROUP BY queue_type
        """
        queue_rows = conn.execute(queue_query, params).fetchall()
        by_queue_type = {
            row["queue_type"]: {"count": row["count"], "total": row["total"]}
            for row in queue_rows
        }

        # By employee
        employee_query = f"""
            SELECT
                sold_by_name,
                COUNT(*) as count,
                COALESCE(SUM(total_due), 0) as total
            FROM transactions
            WHERE {where_sql} AND sold_by_name IS NOT NULL
            GROUP BY sold_by_name
            ORDER BY total DESC
        """
        employee_rows = conn.execute(employee_query, params).fetchall()
        by_employee = {
            row["sold_by_name"]: {"count": row["count"], "total": row["total"]}
            for row in employee_rows
        }

        # Top customers
        customer_query = f"""
            SELECT
                m.name,
                m.member_id,
                COUNT(*) as transactions,
                COALESCE(SUM(t.total_due), 0) as total_spent
            FROM transactions t
            JOIN members m ON t.member_id = m.id
            WHERE {where_sql.replace('date', 't.date')}
            GROUP BY m.id
            ORDER BY total_spent DESC
            LIMIT 10
        """
        try:
            customer_rows = conn.execute(customer_query, params).fetchall()
            top_customers = [
                {
                    "name": row["name"],
                    "member_id": row["member_id"],
                    "transactions": row["transactions"],
                    "total_spent": row["total_spent"],
                }
                for row in customer_rows
            ]
        except:
            top_customers = []

        # Date range
        range_query = "SELECT MIN(date) as start, MAX(date) as end FROM transactions"
        range_row = conn.execute(range_query).fetchone()

        return {
            "period_start": start_date,
            "period_end": end_date,
            "stats": stats,
            "daily_breakdown": daily_breakdown,
            "by_payment_type": by_payment_type,
            "by_queue_type": by_queue_type,
            "by_employee": by_employee,
            "top_customers": top_customers,
        }


@app.get("/api/v1/transactions/{transaction_id}")
def get_transaction(transaction_id: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return dict(row)


@app.get("/api/v1/customers")
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    search: Optional[str] = None,
):
    with get_db() as conn:
        where_clauses = []
        params = []

        if search:
            where_clauses.append("(m.name LIKE ? OR m.member_id LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count
        count_sql = f"""
            SELECT COUNT(DISTINCT m.id)
            FROM members m
            WHERE {where_sql}
        """
        total = conn.execute(count_sql, params).fetchone()[0]

        # Get customers with aggregates
        query_sql = f"""
            SELECT
                m.id,
                m.member_id,
                m.name,
                m.email,
                m.phone,
                COUNT(t.id) as transaction_count,
                COALESCE(SUM(t.total_due), 0) as total_spent,
                MIN(t.date) as first_purchase,
                MAX(t.date) as last_purchase
            FROM members m
            LEFT JOIN transactions t ON t.member_id = m.id
            WHERE {where_sql}
            GROUP BY m.id
            ORDER BY total_spent DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(query_sql, params + [limit, skip]).fetchall()

        customers = [dict(row) for row in rows]

        return {"customers": customers, "total": total, "skip": skip, "limit": limit}


@app.get("/api/v1/employees")
def list_employees():
    with get_db() as conn:
        query = """
            SELECT
                e.id,
                e.employee_id,
                e.name,
                COUNT(t.id) as transaction_count,
                COALESCE(SUM(CASE WHEN t.trans_type != 'Refund' THEN t.total_due ELSE 0 END), 0) as total_sales,
                COALESCE(SUM(CASE WHEN t.trans_type = 'Refund' THEN ABS(t.total_due) ELSE 0 END), 0) as total_refunds,
                COALESCE(SUM(t.total_due), 0) as net_sales,
                COALESCE(AVG(CASE WHEN t.trans_type != 'Refund' THEN t.total_due ELSE NULL END), 0) as average_transaction
            FROM employees e
            LEFT JOIN transactions t ON t.employee_id = e.id
            GROUP BY e.id
            ORDER BY net_sales DESC
        """
        rows = conn.execute(query).fetchall()

        employees = [dict(row) for row in rows]

        return {"employees": employees, "total": len(employees)}


@app.get("/api/v1/ingest/status", response_model=IngestionStatus)
def get_ingest_status():
    with get_db() as conn:
        trans_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        member_count = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        employee_count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]

        date_range = conn.execute(
            "SELECT MIN(date) as start, MAX(date) as end FROM transactions"
        ).fetchone()

        by_type = {}
        type_rows = conn.execute(
            "SELECT trans_type, COUNT(*) as count FROM transactions GROUP BY trans_type"
        ).fetchall()
        for row in type_rows:
            if row["trans_type"]:
                by_type[row["trans_type"]] = row["count"]

        return IngestionStatus(
            transactions=trans_count,
            members=member_count,
            employees=employee_count,
            date_range={"start": date_range["start"], "end": date_range["end"]},
            by_type=by_type,
        )


@app.post("/api/v1/ingest/csv")
def ingest_csv(use_default: bool = Query(False)):
    """Ingest transactions from CSV file"""
    csv_file = CSV_PATH

    if not os.path.exists(csv_file):
        raise HTTPException(status_code=404, detail=f"CSV file not found: {csv_file}")

    inserted = 0
    errors = 0

    with get_db() as conn:
        # Create tables if not exist
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id TEXT UNIQUE,
                name TEXT,
                email TEXT,
                phone TEXT
            );

            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE,
                name TEXT
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blaze_trans_id TEXT,
                trans_no TEXT,
                date TEXT,
                shop TEXT,
                company TEXT,
                trans_type TEXT,
                trans_status TEXT,
                queue_type TEXT,
                order_source TEXT,
                gross_sales REAL DEFAULT 0,
                net_sales REAL DEFAULT 0,
                total_tax REAL DEFAULT 0,
                total_due REAL DEFAULT 0,
                tips REAL DEFAULT 0,
                cogs REAL DEFAULT 0,
                pre_tax_discounts REAL DEFAULT 0,
                after_tax_discount REAL DEFAULT 0,
                payment_type TEXT,
                payment_tendered REAL DEFAULT 0,
                sold_by_name TEXT,
                created_by_name TEXT,
                terminal TEXT,
                region TEXT,
                delivery_city TEXT,
                loyalty_points_spent REAL DEFAULT 0,
                loyalty_points_earned REAL DEFAULT 0,
                compliance_system TEXT,
                compliance_order_id TEXT,
                member_id INTEGER,
                employee_id INTEGER,
                FOREIGN KEY (member_id) REFERENCES members(id),
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );

            CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(date);
            CREATE INDEX IF NOT EXISTS idx_trans_type ON transactions(trans_type);
            CREATE INDEX IF NOT EXISTS idx_trans_no ON transactions(trans_no);
        """)

        member_cache = {}
        employee_cache = {}

        # Load existing members
        for row in conn.execute("SELECT id, member_id FROM members"):
            member_cache[row[1]] = row[0]

        # Load existing employees
        for row in conn.execute("SELECT id, employee_id FROM employees"):
            employee_cache[row[1]] = row[0]

        # Clear existing transactions for re-import
        conn.execute("DELETE FROM transactions")

        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            batch = []
            for row in reader:
                try:
                    # Handle member
                    member_db_id = None
                    blaze_member_id = row.get("Member ID", "").strip()
                    if blaze_member_id:
                        if blaze_member_id not in member_cache:
                            cursor = conn.execute(
                                "INSERT OR IGNORE INTO members (member_id, name) VALUES (?, ?)",
                                (blaze_member_id, row.get("Member Name", "")),
                            )
                            if cursor.lastrowid:
                                member_cache[blaze_member_id] = cursor.lastrowid
                            else:
                                result = conn.execute(
                                    "SELECT id FROM members WHERE member_id = ?",
                                    (blaze_member_id,),
                                ).fetchone()
                                if result:
                                    member_cache[blaze_member_id] = result[0]
                        member_db_id = member_cache.get(blaze_member_id)

                    # Handle employee
                    employee_db_id = None
                    sold_by_name = row.get("Sold By Name", "").strip()
                    if sold_by_name:
                        if sold_by_name not in employee_cache:
                            cursor = conn.execute(
                                "INSERT OR IGNORE INTO employees (employee_id, name) VALUES (?, ?)",
                                (sold_by_name, sold_by_name),
                            )
                            if cursor.lastrowid:
                                employee_cache[sold_by_name] = cursor.lastrowid
                            else:
                                result = conn.execute(
                                    "SELECT id FROM employees WHERE employee_id = ?",
                                    (sold_by_name,),
                                ).fetchone()
                                if result:
                                    employee_cache[sold_by_name] = result[0]
                        employee_db_id = employee_cache.get(sold_by_name)

                    def parse_float(val):
                        if not val or val == "":
                            return 0.0
                        try:
                            return float(val.replace(",", "").replace("$", ""))
                        except:
                            return 0.0

                    batch.append(
                        (
                            row.get("Transaction Id", ""),
                            row.get("Transaction #", ""),
                            row.get("Date", ""),
                            row.get("Shop", ""),
                            row.get("Company", ""),
                            row.get("Transaction Type", ""),
                            row.get("Transaction Status", ""),
                            row.get("Queue Type", ""),
                            row.get("Order Source", ""),
                            parse_float(row.get("Gross Sales", "0")),
                            parse_float(row.get("Net Sales", "0")),
                            parse_float(row.get("Total Tax", "0")),
                            parse_float(row.get("Total Due", "0")),
                            parse_float(row.get("Tips", "0")),
                            parse_float(row.get("COGS", "0")),
                            parse_float(row.get("Pre-Tax Discounts", "0")),
                            parse_float(row.get("After Tax Discount", "0")),
                            row.get("Payment Type", ""),
                            parse_float(row.get("Payment Tendered", "0")),
                            sold_by_name,
                            row.get("Created By Name", ""),
                            row.get("Terminal", ""),
                            row.get("Region", ""),
                            row.get("Delivery City", ""),
                            parse_float(row.get("Loyalty Points Spent", "0")),
                            parse_float(row.get("Loyalty Points Earned", "0")),
                            row.get("Compliance System", ""),
                            row.get("Compliance Order Id", ""),
                            member_db_id,
                            employee_db_id,
                        )
                    )

                    if len(batch) >= 1000:
                        conn.executemany(
                            """
                            INSERT INTO transactions (
                                blaze_trans_id, trans_no, date, shop, company,
                                trans_type, trans_status, queue_type, order_source,
                                gross_sales, net_sales, total_tax, total_due, tips, cogs,
                                pre_tax_discounts, after_tax_discount, payment_type, payment_tendered,
                                sold_by_name, created_by_name, terminal, region, delivery_city,
                                loyalty_points_spent, loyalty_points_earned,
                                compliance_system, compliance_order_id,
                                member_id, employee_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            batch,
                        )
                        inserted += len(batch)
                        batch = []

                except Exception as e:
                    errors += 1
                    continue

            # Insert remaining
            if batch:
                conn.executemany(
                    """
                    INSERT INTO transactions (
                        blaze_trans_id, trans_no, date, shop, company,
                        trans_type, trans_status, queue_type, order_source,
                        gross_sales, net_sales, total_tax, total_due, tips, cogs,
                        pre_tax_discounts, after_tax_discount, payment_type, payment_tendered,
                        sold_by_name, created_by_name, terminal, region, delivery_city,
                        loyalty_points_spent, loyalty_points_earned,
                        compliance_system, compliance_order_id,
                        member_id, employee_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    batch,
                )
                inserted += len(batch)

            conn.commit()

    return {"status": "complete", "inserted": inserted, "errors": errors}


@app.get("/health")
def health():
    return {"status": "ok"}
