"""
Extended employee models: Performance, Activity Log, Time Clock.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Date, Index
from app.core.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class EmployeePerformance(Base):
    """Employee daily performance from master_employee_report.csv."""
    __tablename__ = "employee_performance"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    date = Column(Date, nullable=False, index=True)
    employee_name = Column(String(255), nullable=True, index=True)
    gross_receipts = Column(Float, default=0.0)
    transaction_count = Column(Integer, default=0)
    avg_transaction = Column(Float, default=0.0)
    avg_transaction_time = Column(String(50), nullable=True)
    promotions = Column(Float, default=0.0)
    discounts = Column(Float, default=0.0)
    cash_tendered = Column(Float, default=0.0)
    credit_tendered = Column(Float, default=0.0)
    blazepay_tendered = Column(Float, default=0.0)
    ach_tendered = Column(Float, default=0.0)
    cashless_atm_tendered = Column(Float, default=0.0)
    tips = Column(Float, default=0.0)
    cogs = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_employee_perf_date_emp', 'date', 'employee_name'),
    )


class EmployeeActivity(Base):
    """Employee activity log from employee_activity.csv."""
    __tablename__ = "employee_activity"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    time = Column(DateTime, nullable=True, index=True)
    employee = Column(String(255), nullable=True, index=True)
    action = Column(String(255), nullable=True, index=True)
    category = Column(String(255), nullable=True)
    terminal = Column(String(100), nullable=True)

    __table_args__ = (
        Index('ix_employee_activity_time_emp', 'time', 'employee'),
    )


class TimeClock(Base):
    """Time clock records from time_clock_reports.csv."""
    __tablename__ = "time_clock"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    date = Column(Date, nullable=False, index=True)
    employee = Column(String(255), nullable=True, index=True)
    clock_in = Column(DateTime, nullable=True)
    terminal_in = Column(String(100), nullable=True)
    clock_out = Column(DateTime, nullable=True)
    terminal_out = Column(String(100), nullable=True)
    time_clocked_in = Column(String(50), nullable=True)
    ipad_sessions = Column(Integer, default=0)

    __table_args__ = (
        Index('ix_time_clock_date_emp', 'date', 'employee'),
    )
