"""
Additional Blaze Report Models for comprehensive data ingestion.

These models cover all the CSV report types from Blaze POS:
- Refund History
- Sales Payments
- Sales by Queue
- Received Inventory (Purchase Orders)
- Inventory Reconciliation
- Inventory Actions
- Daily Accounting Summary
- Cash Drawer
- Integrated Payments
- Payments Snapshot
"""

from sqlalchemy import (
    Column, String, DateTime, Float, Integer, Boolean, Text, Date, Index
)
from app.core.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class RefundHistory(Base):
    """Refund history from Blaze refund_history_report.csv."""
    __tablename__ = "refund_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Unique key for deduplication (date + trans_no + product + quantity)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    # Transaction info
    date = Column(Date, nullable=False, index=True)
    trans_no = Column(String(50), nullable=False, index=True)

    # Employee and customer
    employee = Column(String(255), nullable=True)
    customer = Column(String(255), nullable=True)

    # Refund details
    with_inventory = Column(Boolean, default=False)
    product = Column(String(500), nullable=True)
    refund_as = Column(String(50), nullable=True)  # Cash, Credit, etc.
    item_price = Column(Float, default=0.0)
    refund_amount = Column(Float, default=0.0)
    quantity = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_refund_history_date_trans', 'date', 'trans_no'),
    )


class SalesPayment(Base):
    """Sales payments from Blaze sales_payments_report.csv."""
    __tablename__ = "sales_payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Unique key for deduplication
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    # Transaction info
    trans_no = Column(String(50), nullable=False, index=True)
    trans_status = Column(String(50), nullable=True)
    date = Column(Date, nullable=False, index=True)

    # Location
    company = Column(String(500), nullable=True)
    shop = Column(String(255), nullable=True)

    # Payment details
    payment_type = Column(String(50), nullable=True, index=True)
    amount_due = Column(Float, default=0.0)
    cash_back = Column(Float, default=0.0)
    tips = Column(Float, default=0.0)
    change_due = Column(Float, default=0.0)
    payment_tendered = Column(Float, default=0.0)
    payment_fee = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_sales_payments_date_type', 'date', 'payment_type'),
    )


class SalesByQueue(Base):
    """Daily sales aggregated by queue type from sales_by_queue_insights.csv."""
    __tablename__ = "sales_by_queue"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Unique key (date + shop + queue_type)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    # Dimensions
    date = Column(Date, nullable=False, index=True)
    shop = Column(String(255), nullable=True)
    company = Column(String(500), nullable=True)
    queue_type = Column(String(50), nullable=True, index=True)

    # Metrics
    total_due = Column(Float, default=0.0)
    net_sales = Column(Float, default=0.0)
    net_sales_wo_fees = Column(Float, default=0.0)
    num_completed_transactions = Column(Integer, default=0)
    num_refunds = Column(Integer, default=0)

    __table_args__ = (
        Index('ix_sales_by_queue_date_shop', 'date', 'shop'),
    )


class ReceivedInventory(Base):
    """Received inventory/purchase orders from received_inventory.csv."""
    __tablename__ = "received_inventory"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Unique key
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    # Location and dates
    company = Column(String(500), nullable=True)
    shop = Column(String(255), nullable=True)
    date = Column(Date, nullable=False, index=True)
    completed_date = Column(Date, nullable=True)
    delivery_date = Column(Date, nullable=True)
    received_date = Column(Date, nullable=True)
    approved_date = Column(Date, nullable=True)
    po_date = Column(Date, nullable=True)

    # PO details
    po_number = Column(String(100), nullable=True, index=True)
    po_status = Column(String(50), nullable=True)
    transaction_type = Column(String(50), nullable=True)
    sb_number = Column(String(100), nullable=True)
    payment_status = Column(String(50), nullable=True)
    reference = Column(String(255), nullable=True)

    # Product info
    unique_id = Column(String(100), nullable=True)
    product_sku = Column(String(100), nullable=True, index=True)
    product = Column(String(500), nullable=True)
    brand = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    vendor = Column(String(255), nullable=True)
    metrc_tag = Column(String(100), nullable=True)

    # Financials
    paid_amount = Column(Float, default=0.0)
    unpaid_amount = Column(Float, default=0.0)
    unit_cost = Column(Float, default=0.0)
    request_quantity = Column(Float, default=0.0)
    received_quantity = Column(Float, default=0.0)
    request_total_cost = Column(Float, default=0.0)
    received_total_cost = Column(Float, default=0.0)
    final_total_cost = Column(Float, default=0.0)
    excise_tax = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    adjustment_amount = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)
    grand_total = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_received_inventory_date_po', 'date', 'po_number'),
        Index('ix_received_inventory_sku', 'product_sku'),
    )


class InventoryReconciliation(Base):
    """Inventory reconciliation history from inventory_reconciliation_history_insights.csv."""
    __tablename__ = "inventory_reconciliation"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Unique key
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    # Date and location
    date = Column(Date, nullable=False, index=True)
    date_timestamp = Column(DateTime, nullable=True)
    shop = Column(String(255), nullable=True)
    company = Column(String(500), nullable=True)

    # Reconciliation details
    reconciliation_no = Column(String(100), nullable=True, index=True)
    employee_name = Column(String(255), nullable=True)
    inventory_name = Column(String(255), nullable=True)  # Location within shop

    # Product info
    product_name = Column(String(500), nullable=True)
    brand_name = Column(String(255), nullable=True)
    product_sku = Column(String(100), nullable=True, index=True)
    category_name = Column(String(100), nullable=True)
    batch_sku = Column(String(100), nullable=True)
    metrc_tag = Column(String(100), nullable=True)

    # Quantity changes
    new_quantity = Column(Float, default=0.0)
    old_quantity = Column(Float, default=0.0)
    difference = Column(Float, default=0.0)

    # Flags and metadata
    report_loss = Column(Boolean, default=False)
    metrc_adjustment = Column(String(100), nullable=True)
    low_inventory_threshold = Column(Float, default=0.0)
    cost_per_unit = Column(Float, default=0.0)
    cogs = Column(Float, default=0.0)
    pre_package_name = Column(String(255), nullable=True)
    reason = Column(String(100), nullable=True)
    reason_note = Column(Text, nullable=True)

    __table_args__ = (
        Index('ix_inventory_recon_date_sku', 'date', 'product_sku'),
    )


class InventoryAction(Base):
    """Inventory actions from inventory_action_summary.csv."""
    __tablename__ = "inventory_actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Unique key
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    # Date and product
    date = Column(Date, nullable=False, index=True)
    unique_id = Column(String(100), nullable=True)
    metrc_tag = Column(String(100), nullable=True)
    product = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)

    # Action details
    source = Column(String(100), nullable=True)  # Transaction, PurchaseOrder, etc.
    action = Column(String(50), nullable=True, index=True)  # Sale, Refund, AddBatch, etc.
    quantity = Column(Float, default=0.0)
    inventory_value = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_inventory_actions_date_action', 'date', 'action'),
    )


class DailyAccountingSummary(Base):
    """Daily accounting summary from daily_accounting_summary.csv."""
    __tablename__ = "daily_accounting_summary"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Unique key (date + shop + queue_type)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    # Dimensions
    date = Column(Date, nullable=False, index=True)
    shop = Column(String(255), nullable=True, index=True)
    company = Column(String(500), nullable=True)
    queue_type = Column(String(50), nullable=True)

    # Sales by type
    adult_retail_value = Column(Float, default=0.0)
    medical_retail_value = Column(Float, default=0.0)
    non_cannabis_retail_value = Column(Float, default=0.0)
    retail_value_of_sales = Column(Float, default=0.0)

    # Pre-taxes
    pre_al_excise_tax = Column(Float, default=0.0)
    pre_nal_excise_tax = Column(Float, default=0.0)
    pre_city_tax = Column(Float, default=0.0)
    pre_county_tax = Column(Float, default=0.0)
    pre_state_tax = Column(Float, default=0.0)
    pre_federal_tax = Column(Float, default=0.0)

    # Gross sales
    adult_gross_sales = Column(Float, default=0.0)
    medical_gross_sales = Column(Float, default=0.0)
    non_cannabis_gross_sales = Column(Float, default=0.0)
    gross_sales = Column(Float, default=0.0)

    # Fees
    delivery_fee = Column(Float, default=0.0)
    ach_fee = Column(Float, default=0.0)
    blazepay_fee = Column(Float, default=0.0)
    aeropay_fee = Column(Float, default=0.0)
    blazepay_ach_fee = Column(Float, default=0.0)
    cashless_atm_fee = Column(Float, default=0.0)
    cash_fee = Column(Float, default=0.0)
    credit_debit_fee = Column(Float, default=0.0)
    stronghold_fee = Column(Float, default=0.0)

    # Discounts
    pre_tax_discount = Column(Float, default=0.0)

    # Net sales
    adult_net_sales = Column(Float, default=0.0)
    adult_net_sales_wo_fees = Column(Float, default=0.0)
    medical_net_sales = Column(Float, default=0.0)
    medical_net_sales_wo_fees = Column(Float, default=0.0)
    non_cannabis_net_sales = Column(Float, default=0.0)
    non_cannabis_net_sales_wo_fees = Column(Float, default=0.0)
    net_sales = Column(Float, default=0.0)
    net_sales_wo_fees = Column(Float, default=0.0)

    # Post-taxes
    post_al_excise_tax = Column(Float, default=0.0)
    post_nal_excise_tax = Column(Float, default=0.0)
    post_city_tax = Column(Float, default=0.0)
    post_county_tax = Column(Float, default=0.0)
    post_state_tax = Column(Float, default=0.0)
    post_federal_tax = Column(Float, default=0.0)

    # Delivery fee taxes
    delivery_fee_excise_tax = Column(Float, default=0.0)
    city_delivery_fee_tax = Column(Float, default=0.0)
    county_delivery_fee_tax = Column(Float, default=0.0)
    state_delivery_fee_tax = Column(Float, default=0.0)
    federal_delivery_fee_tax = Column(Float, default=0.0)

    # Total taxes
    adult_total_tax = Column(Float, default=0.0)
    medical_total_tax = Column(Float, default=0.0)
    non_cannabis_total_tax = Column(Float, default=0.0)
    total_tax = Column(Float, default=0.0)

    # After tax
    after_tax_discount = Column(Float, default=0.0)
    rounding = Column(Float, default=0.0)
    adjustments = Column(Float, default=0.0)

    # Total due
    adult_total_due = Column(Float, default=0.0)
    medical_total_due = Column(Float, default=0.0)
    non_cannabis_total_due = Column(Float, default=0.0)
    total_due = Column(Float, default=0.0)

    # Tips
    tips = Column(Float, default=0.0)
    blazepay_tips = Column(Float, default=0.0)
    aeropay_tips = Column(Float, default=0.0)
    blazepay_ach_tips = Column(Float, default=0.0)

    # Transaction counts
    num_transactions = Column(Integer, default=0)
    count_completed_sales = Column(Integer, default=0)
    count_refunds = Column(Integer, default=0)
    new_members = Column(Integer, default=0)
    returning_members = Column(Integer, default=0)

    # COGS
    adult_cogs = Column(Float, default=0.0)
    medical_cogs = Column(Float, default=0.0)
    non_cannabis_cogs = Column(Float, default=0.0)

    # Payment tendered by type
    ach_tendered = Column(Float, default=0.0)
    blazepay_tendered = Column(Float, default=0.0)
    aeropay_tendered = Column(Float, default=0.0)
    blazepay_ach_tendered = Column(Float, default=0.0)
    cashless_atm_tendered = Column(Float, default=0.0)
    cash_tendered = Column(Float, default=0.0)
    check_tendered = Column(Float, default=0.0)
    credit_debit_tendered = Column(Float, default=0.0)
    gift_card_tendered = Column(Float, default=0.0)
    birchmount_tendered = Column(Float, default=0.0)
    store_credit_tendered = Column(Float, default=0.0)
    stronghold_tendered = Column(Float, default=0.0)
    payment_tendered = Column(Float, default=0.0)

    # Change due by type
    ach_change_due = Column(Float, default=0.0)
    blazepay_change_due = Column(Float, default=0.0)
    aeropay_change_due = Column(Float, default=0.0)
    blazepay_ach_change_due = Column(Float, default=0.0)
    cashless_atm_change_due = Column(Float, default=0.0)
    cash_change_due = Column(Float, default=0.0)
    check_change_due = Column(Float, default=0.0)
    credit_debit_change_due = Column(Float, default=0.0)
    gift_card_change_due = Column(Float, default=0.0)
    store_credit_change_due = Column(Float, default=0.0)
    stronghold_change_due = Column(Float, default=0.0)
    change_due = Column(Float, default=0.0)

    # Items
    items_sold = Column(Integer, default=0)
    items_refunded = Column(Integer, default=0)
    refund_total_due = Column(Float, default=0.0)

    # Other
    surcharge_fee_tax = Column(Float, default=0.0)
    blazepay_cashback = Column(Float, default=0.0)
    aeropay_cashback = Column(Float, default=0.0)
    blazepay_ach_cashback = Column(Float, default=0.0)
    cashless_atm_cashback = Column(Float, default=0.0)
    untaxed_fee = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_daily_accounting_date_shop', 'date', 'shop'),
    )


class CashDrawer(Base):
    """Cash drawer insights from cash_drawer_insights.csv."""
    __tablename__ = "cash_drawers"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Unique key (date + terminal)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    # Date and terminal
    date = Column(Date, nullable=False, index=True)
    terminal = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    # Cash amounts
    starting_cash = Column(Float, default=0.0)
    ending_cash = Column(Float, default=0.0)
    paid_in = Column(Float, default=0.0)
    paid_out = Column(Float, default=0.0)
    cash_drops = Column(Float, default=0.0)
    expected_in_drawer = Column(Float, default=0.0)
    actual_in_drawer = Column(Float, default=0.0)

    # Sales by payment type
    cash_sales = Column(Float, default=0.0)
    check_sales = Column(Float, default=0.0)
    credit_sales = Column(Float, default=0.0)
    store_credit_sales = Column(Float, default=0.0)
    blazepay_sales = Column(Float, default=0.0)
    ach_sales = Column(Float, default=0.0)
    gift_card_sales = Column(Float, default=0.0)
    cashless_atm_sales = Column(Float, default=0.0)

    # Cash and ATM
    cash_received = Column(Float, default=0.0)
    cashless_atm_received = Column(Float, default=0.0)
    cash_change = Column(Float, default=0.0)
    cashless_atm_change = Column(Float, default=0.0)

    # Refunds
    cash_refunds = Column(Float, default=0.0)
    check_refunds = Column(Float, default=0.0)
    credit_refunds = Column(Float, default=0.0)
    store_credit_refunds = Column(Float, default=0.0)
    blazepay_refunds = Column(Float, default=0.0)
    ach_refunds = Column(Float, default=0.0)
    gift_card_refunds = Column(Float, default=0.0)
    cashless_atm_refunds = Column(Float, default=0.0)

    # Other
    blazepay_cashback = Column(Float, default=0.0)
    cash_voids = Column(Float, default=0.0)
    store_credit_voids = Column(Float, default=0.0)
    gift_card_voids = Column(Float, default=0.0)
    blazepay_tips = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_cash_drawer_date_terminal', 'date', 'terminal'),
    )


class IntegratedPayment(Base):
    """Integrated payments from integrated_payments_report.csv (BlazePay, etc.)."""
    __tablename__ = "integrated_payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Unique key (3rd party ID)
    third_party_id = Column(String(100), unique=True, nullable=False, index=True)

    # Payment service
    payment_service_name = Column(String(100), nullable=True, index=True)

    # Timestamps
    processed_time = Column(DateTime, nullable=True)
    transaction_completion_date = Column(Date, nullable=True, index=True)

    # Transaction details
    transaction_number = Column(String(50), nullable=True, index=True)
    transaction_status = Column(String(50), nullable=True)

    # Customer
    customer = Column(String(255), nullable=True)

    # Amounts
    total_due = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    tip = Column(Float, default=0.0)
    cashback = Column(Float, default=0.0)
    payment_fee = Column(Float, default=0.0)
    gross_payment = Column(Float, default=0.0)

    # Employee and terminal
    employee = Column(String(255), nullable=True)
    terminal_id = Column(String(100), nullable=True)
    terminal_name = Column(String(100), nullable=True)
    third_party_terminal_id = Column(String(100), nullable=True)
    payment_id = Column(String(100), nullable=True)

    __table_args__ = (
        Index('ix_integrated_payments_date', 'transaction_completion_date'),
    )


class PaymentsSnapshot(Base):
    """Payments snapshot from payments_snapshot.csv."""
    __tablename__ = "payments_snapshot"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Unique key
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    # Date and location
    date = Column(Date, nullable=False, index=True)
    shop = Column(String(255), nullable=True)
    company = Column(String(500), nullable=True)

    # Payment details
    payment_type = Column(String(50), nullable=True, index=True)
    payment_type_usage = Column(Integer, default=0)
    queue_type = Column(String(50), nullable=True)

    # Amounts
    total_due = Column(Float, default=0.0)
    cash_back = Column(Float, default=0.0)
    change_due = Column(Float, default=0.0)
    transaction_fee = Column(Float, default=0.0)
    payment_received = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_payments_snapshot_date_type', 'date', 'payment_type'),
    )
