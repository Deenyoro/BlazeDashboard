from sqlalchemy import (
    Column, String, DateTime, Float, Integer, Boolean, Text, ForeignKey, Index, Date
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class Product(Base):
    """Product master data - unique products from Blaze inventory."""
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    blaze_product_id = Column(String(50), unique=True, nullable=True, index=True)
    sku = Column(String(100), nullable=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    brand = Column(String(255), nullable=True, index=True)
    unit_price = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)

    product_sales = relationship("ProductSale", back_populates="product")


class ProductSale(Base):
    """Product-level sales data from Completed Sales Details Report."""
    __tablename__ = "product_sales"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Unique key for deduplication
    trans_no = Column(String(50), nullable=False, index=True)
    metrc_sale_id = Column(String(100), nullable=True, index=True)
    metrc_tag = Column(String(100), nullable=True, index=True)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)  # Hash for deduplication

    # Date for easier querying
    sale_date = Column(DateTime, nullable=False, index=True)

    # Transaction info
    trans_type = Column(String(50), nullable=True)
    trans_status = Column(String(50), nullable=True)
    queue_type = Column(String(50), nullable=True)

    # Product reference
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True)
    product = relationship("Product", back_populates="product_sales")
    product_name = Column(String(500), nullable=True)
    sku = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    brand = Column(String(255), nullable=True)
    vendor = Column(String(255), nullable=True)
    batch = Column(String(100), nullable=True)

    # Cannabis flag
    is_cannabis = Column(Boolean, default=True)

    # Quantity and pricing
    quantity = Column(Float, default=0.0)
    cogs = Column(Float, default=0.0)
    retail_value = Column(Float, default=0.0)
    retail_price = Column(Float, default=0.0)
    effective_retail_price = Column(Float, default=0.0)
    net_sales = Column(Float, default=0.0)
    product_discounts = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)
    cart_discounts = Column(Float, default=0.0)
    total_discount = Column(Float, default=0.0)
    final_subtotal = Column(Float, default=0.0)

    # Taxes
    pre_al_excise_tax = Column(Float, default=0.0)
    pre_nal_excise_tax = Column(Float, default=0.0)
    pre_ohio_excise_tax = Column(Float, default=0.0)
    pre_county_tax = Column(Float, default=0.0)
    pre_state_tax = Column(Float, default=0.0)
    pre_state_excise_tax = Column(Float, default=0.0)
    post_al_excise_tax = Column(Float, default=0.0)
    post_nal_excise_tax = Column(Float, default=0.0)
    ohio_excise_tax = Column(Float, default=0.0)
    county_tax = Column(Float, default=0.0)
    state_tax = Column(Float, default=0.0)
    state_excise_tax = Column(Float, default=0.0)
    total_tax = Column(Float, default=0.0)
    after_tax_discount = Column(Float, default=0.0)

    # Fees
    delivery_fees = Column(Float, default=0.0)
    credit_card_fees = Column(Float, default=0.0)
    cashless_atm_fee = Column(Float, default=0.0)
    ach_fee = Column(Float, default=0.0)
    blazepay_fee = Column(Float, default=0.0)

    # Tips
    tips = Column(Float, default=0.0)
    manual_tips = Column(Float, default=0.0)

    # Payment
    blazepay_id = Column(String(100), nullable=True)
    cashless_atm_received = Column(Float, default=0.0)
    cashless_atm_change = Column(Float, default=0.0)
    cash_received = Column(Float, default=0.0)
    cash_change = Column(Float, default=0.0)
    gross_receipt = Column(Float, default=0.0)
    rounded_amount = Column(Float, default=0.0)
    payment_type = Column(String(50), nullable=True)
    terminal = Column(String(100), nullable=True)

    # Employee
    sold_by = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_date = Column(DateTime, nullable=True)
    prepared_by = Column(String(255), nullable=True)
    prepared_date = Column(DateTime, nullable=True)
    packed_by = Column(String(255), nullable=True)
    packed_date = Column(DateTime, nullable=True)

    # Promotion
    promotions = Column(Text, nullable=True)

    # Member info
    member_name = Column(String(255), nullable=True)
    member_id = Column(String(50), nullable=True, index=True)  # Blaze Member ID
    member_group = Column(String(100), nullable=True)
    consumer_tax_type = Column(String(50), nullable=True)
    marketing_source = Column(String(255), nullable=True)
    zip_code = Column(String(20), nullable=True)
    member_state = Column(String(100), nullable=True)  # Sometimes contains city names
    date_joined = Column(DateTime, nullable=True)
    gender = Column(String(20), nullable=True)
    dob = Column(DateTime, nullable=True)
    age = Column(Integer, nullable=True)
    loyalty_points = Column(Float, default=0.0)

    # Notes and tags
    discount_notes = Column(Text, nullable=True)
    order_tags = Column(Text, nullable=True)

    # Region and compliance
    region_name = Column(String(100), nullable=True)

    # Payment method columns
    blazepay_amount = Column(Float, default=0.0)
    cashless_atm_amount = Column(Float, default=0.0)
    cash_amount = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_product_sales_trans_product', 'trans_no', 'product_name'),
        Index('ix_product_sales_date_category', 'sale_date', 'category'),
        Index('ix_product_sales_metrc', 'metrc_sale_id', 'metrc_tag'),
    )


class InventorySnapshot(Base):
    """Inventory snapshots from Blaze Inventory Report."""
    __tablename__ = "inventory_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Snapshot date for deduplication (one snapshot per product per day)
    snapshot_date = Column(Date, nullable=False, index=True)

    # Product info
    blaze_product_id = Column(String(50), nullable=True, index=True)
    sku = Column(String(100), nullable=True, index=True)
    product_name = Column(String(500), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    brand = Column(String(255), nullable=True)

    # Inventory levels
    quantity_on_hand = Column(Float, default=0.0)
    quantity_available = Column(Float, default=0.0)
    quantity_reserved = Column(Float, default=0.0)

    # Valuation
    unit_cost = Column(Float, default=0.0)
    total_value = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_inventory_date_product', 'snapshot_date', 'sku'),
    )


class DiscountUsage(Base):
    """Discount/promotion usage from Blaze Discounts Report."""
    __tablename__ = "discount_usage"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Unique key for deduplication
    blaze_trans_id = Column(String(50), nullable=False, index=True)
    discount_id = Column(String(100), nullable=True)

    # Date
    usage_date = Column(DateTime, nullable=False, index=True)

    # Discount info
    discount_name = Column(String(255), nullable=False)
    discount_type = Column(String(50), nullable=True)  # Percentage, Fixed, BOGO
    discount_amount = Column(Float, default=0.0)
    discount_percent = Column(Float, default=0.0)

    # What it was applied to
    applied_to_product = Column(String(500), nullable=True)
    applied_to_category = Column(String(100), nullable=True)

    # Employee
    applied_by = Column(String(255), nullable=True)

    __table_args__ = (
        Index('ix_discount_date_name', 'usage_date', 'discount_name'),
    )


class Member(Base):
    __tablename__ = "members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    blaze_member_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    member_group = Column(String(100), nullable=True)
    consumer_tax_type = Column(String(50), nullable=True)

    transactions = relationship("Transaction", back_populates="member")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), unique=True, nullable=False, index=True)

    transactions_sold = relationship(
        "Transaction", back_populates="sold_by_employee", foreign_keys="Transaction.sold_by_id"
    )
    transactions_created = relationship(
        "Transaction", back_populates="created_by_employee", foreign_keys="Transaction.created_by_id"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Blaze identifiers
    blaze_trans_id = Column(String(50), unique=True, nullable=False, index=True)
    trans_no = Column(String(50), nullable=True, index=True)

    # Timestamps
    date = Column(DateTime, nullable=False, index=True)
    created_date = Column(DateTime, nullable=True)
    prepared_date = Column(DateTime, nullable=True)
    packed_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)

    # Location/Shop
    shop = Column(String(255), nullable=True, index=True)
    company = Column(String(500), nullable=True)
    terminal = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    delivery_city = Column(String(100), nullable=True, index=True)

    # Transaction type/status
    trans_type = Column(String(50), nullable=True, index=True)  # Sale, Refund
    trans_status = Column(String(50), nullable=True, index=True)  # Completed, RefundWithInventory
    queue_type = Column(String(50), nullable=True, index=True)  # WalkIn, Delivery, Online
    order_source = Column(String(100), nullable=True)

    # Member/Customer
    member_id = Column(String(36), ForeignKey("members.id"), nullable=True)
    member = relationship("Member", back_populates="transactions")

    # Financial - Sales
    retail_value = Column(Float, default=0.0)
    gross_sales = Column(Float, default=0.0)
    net_sales = Column(Float, default=0.0)
    net_sales_wo_fees = Column(Float, default=0.0)
    delivery_fees = Column(Float, default=0.0)

    # Financial - Discounts
    pre_tax_discounts = Column(Float, default=0.0)
    after_tax_discount = Column(Float, default=0.0)
    product_promotions = Column(Text, nullable=True)
    cart_promotions = Column(Text, nullable=True)
    discount_notes = Column(Text, nullable=True)

    # Financial - Taxes (Pre)
    pre_al_excise_tax = Column(Float, default=0.0)
    pre_nal_excise_tax = Column(Float, default=0.0)
    pre_city_tax = Column(Float, default=0.0)
    pre_county_tax = Column(Float, default=0.0)
    pre_state_tax = Column(Float, default=0.0)
    pre_fed_tax = Column(Float, default=0.0)

    # Financial - Taxes (Post)
    post_al_excise_tax = Column(Float, default=0.0)
    post_nal_excise_tax = Column(Float, default=0.0)
    city_tax = Column(Float, default=0.0)
    county_tax = Column(Float, default=0.0)
    state_tax = Column(Float, default=0.0)
    federal_tax = Column(Float, default=0.0)

    # Financial - Delivery Fee Taxes
    delivery_fee_excise_tax = Column(Float, default=0.0)
    city_delivery_fee_tax = Column(Float, default=0.0)
    county_delivery_fee_tax = Column(Float, default=0.0)
    state_delivery_fee_tax = Column(Float, default=0.0)
    fed_delivery_fee_tax = Column(Float, default=0.0)

    # Financial - Totals
    total_tax = Column(Float, default=0.0)
    rounded_amount = Column(Float, default=0.0)
    adjustments = Column(Float, default=0.0)
    payment_fee = Column(Float, default=0.0)
    total_due = Column(Float, default=0.0)
    surcharge_fee_tax = Column(Float, default=0.0)
    untaxed_fee = Column(Float, default=0.0)

    # Tips
    tips = Column(Float, default=0.0)
    blazepay_tips = Column(Float, default=0.0)

    # Cost/Margin
    cogs = Column(Float, default=0.0)

    # Payment
    payment_type = Column(String(50), nullable=True, index=True)
    blazepay_id = Column(String(100), nullable=True)
    payment_tendered = Column(Float, default=0.0)
    cash_change = Column(Float, default=0.0)
    cashless_atm_change = Column(Float, default=0.0)
    change_due = Column(Float, default=0.0)

    # Employee references
    sold_by_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    sold_by_employee = relationship("Employee", back_populates="transactions_sold", foreign_keys=[sold_by_id])
    sold_by_name = Column(String(255), nullable=True)

    created_by_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    created_by_employee = relationship("Employee", back_populates="transactions_created", foreign_keys=[created_by_id])
    created_by_name = Column(String(255), nullable=True)

    prepared_by = Column(String(255), nullable=True)
    packed_by = Column(String(255), nullable=True)

    # Marketing
    marketing_source = Column(String(255), nullable=True)
    order_tags = Column(Text, nullable=True)

    # Loyalty
    loyalty_points_spent = Column(Float, default=0.0)
    loyalty_points_earned = Column(Float, default=0.0)

    # Compliance
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
