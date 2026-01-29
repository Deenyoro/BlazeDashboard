"""
Extended member models: Performance, Inactive, Marketing.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Date, Index
from app.core.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class MemberPerformance(Base):
    """Member performance metrics from member_performance.csv."""
    __tablename__ = "member_performance"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    member_id = Column(String(100), unique=True, nullable=False, index=True)
    member_name = Column(String(255), nullable=True)
    member_phone = Column(String(50), nullable=True)
    marketing_src = Column(String(255), nullable=True)
    member_group = Column(String(100), nullable=True)
    date_joined = Column(DateTime, nullable=True)
    consumer_type = Column(String(50), nullable=True)
    loyalty_points = Column(Float, default=0.0)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    last_visited = Column(DateTime, nullable=True)
    num_visits = Column(Integer, default=0)
    num_sales = Column(Integer, default=0)
    num_refunds = Column(Integer, default=0)
    gross_sales_receipts = Column(Float, default=0.0)
    gross_refund_receipts = Column(Float, default=0.0)
    avg_sales_receipts = Column(Float, default=0.0)
    avg_refund_receipts = Column(Float, default=0.0)


class InactiveMember(Base):
    """Inactive members from inactive_members.csv."""
    __tablename__ = "inactive_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    cell_phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    last_visit = Column(DateTime, nullable=True, index=True)
    rec_exp_date = Column(Date, nullable=True)
    total_amount_spent = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_inactive_members_name', 'first_name', 'last_name'),
    )


class MarketingContact(Base):
    """Marketing contacts from marketing.csv."""
    __tablename__ = "marketing_contacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    membership_group = Column(String(100), nullable=True)
    marketing_source = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    loyalty_points = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_marketing_contacts_name', 'first_name', 'last_name'),
    )
