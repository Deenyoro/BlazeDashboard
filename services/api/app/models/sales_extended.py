"""
Extended sales, inventory, and financial models.
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, Date, DateTime, Index
from app.core.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class DeliverySale(Base):
    """Delivery sales from delivery_sales.csv."""
    __tablename__ = "delivery_sales"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    date = Column(DateTime, nullable=True, index=True)
    transaction_id = Column(String(100), nullable=True, index=True)
    metrc_id = Column(String(100), nullable=True)
    metrc_delivery_id = Column(String(100), nullable=True)
    customer_first_name = Column(String(255), nullable=True)
    customer_last_name = Column(String(255), nullable=True)
    dob = Column(Date, nullable=True)
    delivery_address = Column(String(500), nullable=True)
    city = Column(String(255), nullable=True)
    zip_code = Column(String(20), nullable=True)
    region = Column(String(100), nullable=True)
    employee = Column(String(255), nullable=True)
    order_source = Column(String(100), nullable=True)
    sales = Column(Float, default=0.0)
    discounts = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)
    al_excise = Column(Float, default=0.0)
    nal_excise = Column(Float, default=0.0)
    ohio_excise_tax = Column(Float, default=0.0)
    county_tax = Column(Float, default=0.0)
    state_tax = Column(Float, default=0.0)
    state_excise_tax = Column(Float, default=0.0)
    gross_receipts = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_delivery_sales_date', 'date'),
    )


class CanceledVoidSale(Base):
    """Canceled/void orders from total_sales_canceled_void_orders.csv."""
    __tablename__ = "canceled_void_sales"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    date = Column(DateTime, nullable=True, index=True)
    member = Column(String(255), nullable=True)
    transaction_no = Column(String(50), nullable=True, index=True)
    trans_type = Column(String(50), nullable=True)
    trans_status = Column(String(50), nullable=True)
    queue_type = Column(String(50), nullable=True)
    member_id = Column(String(100), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    consumer_tax_type = Column(String(50), nullable=True)
    cogs = Column(Float, default=0.0)
    retail_value = Column(Float, default=0.0)
    discounts = Column(Float, default=0.0)
    net_sales = Column(Float, default=0.0)
    total_tax = Column(Float, default=0.0)
    delivery_fees = Column(Float, default=0.0)
    tips = Column(Float, default=0.0)
    after_tax_discount = Column(Float, default=0.0)
    gross_receipt = Column(Float, default=0.0)
    employee = Column(String(255), nullable=True)
    terminal = Column(String(100), nullable=True)
    payment_type = Column(String(50), nullable=True)
    promotions = Column(Text, nullable=True)
    marketing_source = Column(String(255), nullable=True)
    gross_sales = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_canceled_void_date', 'date'),
    )


class UncompleteSale(Base):
    """Uncomplete orders from total_sales_with_uncomplete_orders.csv."""
    __tablename__ = "uncomplete_sales"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    date = Column(DateTime, nullable=True, index=True)
    member = Column(String(255), nullable=True)
    transaction_no = Column(String(50), nullable=True, index=True)
    trans_type = Column(String(50), nullable=True)
    trans_status = Column(String(50), nullable=True)
    consumer_tax_type = Column(String(50), nullable=True)
    cogs = Column(Float, default=0.0)
    retail_value = Column(Float, default=0.0)
    discounts = Column(Float, default=0.0)
    total_tax = Column(Float, default=0.0)
    delivery_fees = Column(Float, default=0.0)
    tips = Column(Float, default=0.0)
    after_tax_discount = Column(Float, default=0.0)
    gross_receipt = Column(Float, default=0.0)
    employee = Column(String(255), nullable=True)
    terminal = Column(String(100), nullable=True)
    payment_type = Column(String(50), nullable=True)
    promotions = Column(Text, nullable=True)
    marketing_source = Column(String(255), nullable=True)
    metrc_id = Column(String(100), nullable=True)

    __table_args__ = (
        Index('ix_uncomplete_date', 'date'),
    )


class PromotionsActivity(Base):
    """Promotions activity from promotions_activity.csv."""
    __tablename__ = "promotions_activity"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    date = Column(DateTime, nullable=True, index=True)
    transaction_no = Column(String(50), nullable=True, index=True)
    reward_system = Column(String(100), nullable=True)
    promo_name = Column(String(500), nullable=True)
    promo_type = Column(String(100), nullable=True)
    code_used = Column(String(100), nullable=True)
    cash_value = Column(Float, default=0.0)
    employee = Column(String(255), nullable=True)
    member = Column(String(255), nullable=True)


class ProfitLoss(Base):
    """Profit/loss report from profit_loss_report.csv."""
    __tablename__ = "profit_loss"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    date = Column(Date, nullable=False, index=True)
    gross_receipts = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    loss = Column(Float, default=0.0)
    profit = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    margin_pct = Column(Float, default=0.0)


class PurchaseOrderByCategory(Base):
    """Purchase orders by category from purchase_order_by_category.csv."""
    __tablename__ = "purchase_order_by_category"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    po_date = Column(Date, nullable=True, index=True)
    vendor_name = Column(String(255), nullable=True, index=True)
    product_category = Column(String(100), nullable=True)
    cogs = Column(Float, default=0.0)
    excise_tax = Column(Float, default=0.0)
    po_number = Column(String(100), nullable=True)


class ReturnToVendor(Base):
    """Return to vendor from return_to_vendor.csv."""
    __tablename__ = "return_to_vendor"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    date = Column(Date, nullable=True, index=True)
    vendor = Column(String(255), nullable=True)
    product_category = Column(String(100), nullable=True)
    product = Column(String(500), nullable=True)
    low_inventory_threshold = Column(Float, default=0.0)
    batch_sku = Column(String(100), nullable=True)
    quantity = Column(Float, default=0.0)


class RefundHistoryDetail(Base):
    """Detailed refund history from refund_history.csv (RETAIL version)."""
    __tablename__ = "refund_history_detail"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    date = Column(Date, nullable=False, index=True)
    transaction_no = Column(String(50), nullable=True, index=True)
    employee = Column(String(255), nullable=True)
    customer = Column(String(255), nullable=True)
    with_inventory = Column(Boolean, default=False)
    refund_as = Column(String(50), nullable=True)
    refund_amount = Column(Float, default=0.0)
    product = Column(String(500), nullable=True)
    quantity = Column(Float, default=0.0)


class PaidInOutActivity(Base):
    """Paid in/out activity from paidinout_activity.csv."""
    __tablename__ = "paidinout_activity"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    date = Column(Date, nullable=True, index=True)
    cash_drawer_date = Column(Date, nullable=True)
    employee = Column(String(255), nullable=True)
    terminal = Column(String(100), nullable=True)
    starting_cash = Column(Float, default=0.0)
    day_end = Column(Float, default=0.0)
    daily_sales = Column(Float, default=0.0)
    paid_in = Column(Float, default=0.0)
    paid_out = Column(Float, default=0.0)
    cash_drop = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)


class InventoryAging(Base):
    """Inventory aging from inventory_aging.csv."""
    __tablename__ = "inventory_aging"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    product_sku = Column(String(100), nullable=True, index=True)
    product_name = Column(String(500), nullable=True)
    product_category = Column(String(100), nullable=True)
    low_inventory_threshold = Column(Float, default=0.0)
    days_0_30_qty = Column(Float, default=0.0)
    days_0_30_val = Column(Float, default=0.0)
    days_31_45_qty = Column(Float, default=0.0)
    days_31_45_val = Column(Float, default=0.0)
    days_46_60_qty = Column(Float, default=0.0)
    days_46_60_val = Column(Float, default=0.0)
    days_61_90_qty = Column(Float, default=0.0)
    days_61_90_val = Column(Float, default=0.0)
    days_90_plus_qty = Column(Float, default=0.0)
    days_90_plus_val = Column(Float, default=0.0)


class InventoryDistribution(Base):
    """Inventory distribution from inventory_distribution.csv."""
    __tablename__ = "inventory_distribution"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    product = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    brand = Column(String(255), nullable=True)
    unit_type = Column(String(50), nullable=True)
    low_inventory_threshold = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    exchange = Column(Float, default=0.0)
    fulfillment = Column(Float, default=0.0)
    quarantine = Column(Float, default=0.0)
    safe = Column(Float, default=0.0)
    vault = Column(Float, default=0.0)


class InventoryValuation(Base):
    """Inventory valuation from inventory_log_valuation.csv."""
    __tablename__ = "inventory_valuation"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    product_name = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    cannabis_type = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    avg_unit_cost = Column(Float, default=0.0)
    avg_excise_cost = Column(Float, default=0.0)
    unit_excise_cost = Column(Float, default=0.0)
    avg_retail_price = Column(Float, default=0.0)
    avg_profit = Column(Float, default=0.0)
    avg_margin_pct = Column(Float, default=0.0)
    avg_markup_pct = Column(Float, default=0.0)
    total_available_qty = Column(Float, default=0.0)
    total_available_cogs = Column(Float, default=0.0)
    total_available_excise = Column(Float, default=0.0)
    total_available_cogs_excise = Column(Float, default=0.0)


class InventoryTransfer(Base):
    """Inventory transfers from inventory_transfer_log.csv."""
    __tablename__ = "inventory_transfers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    date = Column(DateTime, nullable=True, index=True)
    employee = Column(String(255), nullable=True)
    product = Column(String(500), nullable=True)
    origin_shop = Column(String(255), nullable=True)
    origin_inventory = Column(String(255), nullable=True)
    destination_shop = Column(String(255), nullable=True)
    destination = Column(String(255), nullable=True)
    amount = Column(Float, default=0.0)


class SellThrough(Base):
    """Sell-through report from sell_through_report.csv."""
    __tablename__ = "sell_through"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    product_id = Column(String(100), nullable=True, index=True)
    product_name = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)
    low_inventory_threshold = Column(Float, default=0.0)
    avg_qty_sold_per_day = Column(Float, default=0.0)
    days_remaining = Column(Float, default=0.0)
    qty_on_hand = Column(Float, default=0.0)


class CurrentInventory(Base):
    """Current inventory from single_inventory.csv."""
    __tablename__ = "current_inventory"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    product = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=True)
    low_inventory_threshold = Column(Float, default=0.0)
    current_quantity = Column(Float, default=0.0)
    current_cogs = Column(Float, default=0.0)
    sold_quantity = Column(Float, default=0.0)
    sold_cogs = Column(Float, default=0.0)
    current_prepackages = Column(Float, default=0.0)
    current_pack_cogs = Column(Float, default=0.0)
    sold_prepackages = Column(Float, default=0.0)
    sold_pack_cogs = Column(Float, default=0.0)
    retail_price = Column(Float, default=0.0)
    retail_value = Column(Float, default=0.0)


class SalesByCity(Base):
    """Sales by city from sales_by_city.csv."""
    __tablename__ = "sales_by_city"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    city = Column(String(255), nullable=True, index=True)
    state = Column(String(100), nullable=True)
    transactions = Column(Integer, default=0)
    subtotal_sales = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    total_taxes = Column(Float, default=0.0)
    delivery_fee = Column(Float, default=0.0)
    tips = Column(Float, default=0.0)
    gross_receipts = Column(Float, default=0.0)
    percentage_of_sales = Column(Float, default=0.0)


class SalesByHour(Base):
    """Sales by hour from sales_by_hour.csv."""
    __tablename__ = "sales_by_hour"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    hour = Column(String(20), nullable=True)
    recreational_sales = Column(Float, default=0.0)
    medical_sales = Column(Float, default=0.0)
    total_sales = Column(Float, default=0.0)
    recreational_discounts = Column(Float, default=0.0)
    medicinal_discounts = Column(Float, default=0.0)
    total_discounts = Column(Float, default=0.0)
    gross_receipts = Column(Float, default=0.0)
    num_transactions = Column(Integer, default=0)


class SalesByProduct(Base):
    """Sales by product from sales_by_product.csv."""
    __tablename__ = "sales_by_product"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    product = Column(String(500), nullable=True)
    sku = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    vendor = Column(String(255), nullable=True)
    brand = Column(String(255), nullable=True)
    product_tags = Column(Text, nullable=True)
    units_sold = Column(Float, default=0.0)
    cogs = Column(Float, default=0.0)
    retail_value = Column(Float, default=0.0)
    total_discounts = Column(Float, default=0.0)
    product_discounts = Column(Float, default=0.0)
    cart_discounts = Column(Float, default=0.0)
    net_sales = Column(Float, default=0.0)
    subtotal_sales = Column(Float, default=0.0)
    total_tax = Column(Float, default=0.0)
    delivery_fees = Column(Float, default=0.0)
    after_tax_discounts = Column(Float, default=0.0)
    margin = Column(Float, default=0.0)
    revenue_per_unit = Column(Float, default=0.0)
    pct_of_sales = Column(Float, default=0.0)


class SalesByProductCategory(Base):
    """Sales by product category from sales_by_product_category.csv."""
    __tablename__ = "sales_by_product_category"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    product_category = Column(String(100), nullable=True, index=True)
    num_trans = Column(Integer, default=0)
    cogs = Column(Float, default=0.0)
    retail_value = Column(Float, default=0.0)
    total_discounts = Column(Float, default=0.0)
    product_discounts = Column(Float, default=0.0)
    subtotal_sales = Column(Float, default=0.0)
    cart_discounts = Column(Float, default=0.0)
    net_sales = Column(Float, default=0.0)
    total_tax = Column(Float, default=0.0)
    delivery_fees = Column(Float, default=0.0)
    after_tax_discounts = Column(Float, default=0.0)
    gross_receipt = Column(Float, default=0.0)
    units_sold = Column(Float, default=0.0)


class SalesByVendor(Base):
    """Sales by vendor from sales_by_vendor.csv."""
    __tablename__ = "sales_by_vendor"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    vendor = Column(String(255), nullable=True, index=True)
    transaction_type = Column(String(50), nullable=True)
    subtotal_sales = Column(Float, default=0.0)
    delivery_fees = Column(Float, default=0.0)
    discounts = Column(Float, default=0.0)
    after_tax_discount = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    gross_receipt = Column(Float, default=0.0)


class SalesByConsumerType(Base):
    """Sales by consumer type from sales_by_consumer_type.csv."""
    __tablename__ = "sales_by_consumer_type"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    breakdown = Column(String(100), nullable=True)
    cannabis_retail_value = Column(Float, default=0.0)
    non_cannabis_retail_value = Column(Float, default=0.0)
    cannabis_discounts = Column(Float, default=0.0)
    non_cannabis_discounts = Column(Float, default=0.0)
    total_discounts = Column(Float, default=0.0)
    after_tax_discount = Column(Float, default=0.0)
    gross_revenue = Column(Float, default=0.0)
    total_tax = Column(Float, default=0.0)
    delivery_fees = Column(Float, default=0.0)
    tips = Column(Float, default=0.0)
    gross_receipt = Column(Float, default=0.0)
    cogs = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)
    num_visits = Column(Integer, default=0)


class EmployeeSalesByProduct(Base):
    """Employee sales by product from employee_by_sales_by_product.csv."""
    __tablename__ = "employee_sales_by_product"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    product = Column(String(500), nullable=True)
    employee = Column(String(255), nullable=True, index=True)
    quantity = Column(Float, default=0.0)


class ProductsByVendor(Base):
    """Products by vendor from products_by_vendor.csv."""
    __tablename__ = "products_by_vendor"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    vendor = Column(String(255), nullable=True, index=True)
    contact_first_name = Column(String(255), nullable=True)
    contact_surname = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    brand = Column(String(255), nullable=True)
    product = Column(String(500), nullable=True)
    quantity_sold = Column(Float, default=0.0)
    quantity_in_stock = Column(Float, default=0.0)
    sales = Column(Float, default=0.0)


class ProductSalesByInventory(Base):
    """Product sales by inventory location from product_sales_by_inventory.csv."""
    __tablename__ = "product_sales_by_inventory"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    product = Column(String(500), nullable=True)
    sku = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True)
    vendor = Column(String(255), nullable=True)
    brand = Column(String(255), nullable=True)
    product_tags = Column(Text, nullable=True)
    total_units_sold = Column(Float, default=0.0)
    quarantine_units_sold = Column(Float, default=0.0)
    vault_units_sold = Column(Float, default=0.0)
    fulfillment_units_sold = Column(Float, default=0.0)
    exchange_units_sold = Column(Float, default=0.0)
    sales_floor_units_sold = Column(Float, default=0.0)
    safe_units_sold = Column(Float, default=0.0)
    delivery_units_sold = Column(Float, default=0.0)


class ProductSellByExpire(Base):
    """Product sell-by/expiration from product_sell_by_expire.csv."""
    __tablename__ = "product_sell_by_expire"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    product_category = Column(String(100), nullable=True, index=True)
    product_name = Column(String(500), nullable=True)
    status = Column(String(50), nullable=True)
    batch_id = Column(String(100), nullable=True)
    sell_by_date = Column(Date, nullable=True, index=True)
    qty_remaining = Column(Float, default=0.0)
    low_inventory_threshold = Column(Float, default=0.0)
    unit_type = Column(String(50), nullable=True)
