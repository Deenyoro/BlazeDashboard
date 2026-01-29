from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class MemberResponse(BaseModel):
    id: str
    blaze_member_id: str
    name: Optional[str] = None
    member_group: Optional[str] = None
    consumer_tax_type: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    id: str
    blaze_trans_id: str
    trans_no: Optional[str] = None
    date: datetime
    shop: Optional[str] = None
    company: Optional[str] = None

    # Type/Status
    trans_type: Optional[str] = None
    trans_status: Optional[str] = None
    queue_type: Optional[str] = None
    order_source: Optional[str] = None

    # Financial
    gross_sales: float = 0.0
    net_sales: float = 0.0
    total_tax: float = 0.0
    total_due: float = 0.0
    tips: float = 0.0
    cogs: float = 0.0

    # Discounts
    pre_tax_discounts: float = 0.0
    after_tax_discount: float = 0.0

    # Payment
    payment_type: Optional[str] = None
    payment_tendered: float = 0.0

    # Employee
    sold_by_name: Optional[str] = None
    created_by_name: Optional[str] = None

    # Location
    terminal: Optional[str] = None
    region: Optional[str] = None
    delivery_city: Optional[str] = None

    # Loyalty
    loyalty_points_spent: float = 0.0
    loyalty_points_earned: float = 0.0

    # Compliance
    compliance_system: Optional[str] = None
    compliance_order_id: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
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


class DailySales(BaseModel):
    date: str
    transaction_count: int
    gross_sales: float
    net_sales: float
    total_tax: float
    tips: float
    refunds: float


class SalesOverview(BaseModel):
    period_start: datetime
    period_end: datetime
    stats: TransactionStats
    daily_breakdown: List[DailySales]
    by_payment_type: dict
    by_queue_type: dict
    by_employee: dict
    top_customers: List[dict]


class ProductSaleResponse(BaseModel):
    """Product-level sale detail."""
    id: str
    trans_no: str
    sale_date: datetime

    # Product info
    product_name: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    vendor: Optional[str] = None
    batch: Optional[str] = None
    is_cannabis: bool = True

    # Quantity and pricing
    quantity: float = 0.0
    retail_price: float = 0.0
    effective_retail_price: float = 0.0
    net_sales: float = 0.0
    cogs: float = 0.0

    # Discounts
    product_discounts: float = 0.0
    cart_discounts: float = 0.0
    total_discount: float = 0.0

    # Taxes
    total_tax: float = 0.0

    # Compliance
    metrc_tag: Optional[str] = None
    metrc_sale_id: Optional[str] = None

    # Promotions
    promotions: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionDetailResponse(BaseModel):
    """Full transaction detail including line items."""
    # Transaction header
    id: str
    blaze_trans_id: str
    trans_no: Optional[str] = None
    date: datetime
    created_date: Optional[datetime] = None
    prepared_date: Optional[datetime] = None
    packed_date: Optional[datetime] = None

    # Location
    shop: Optional[str] = None
    company: Optional[str] = None
    terminal: Optional[str] = None
    region: Optional[str] = None
    delivery_city: Optional[str] = None

    # Type/Status
    trans_type: Optional[str] = None
    trans_status: Optional[str] = None
    queue_type: Optional[str] = None
    order_source: Optional[str] = None

    # Customer
    member_name: Optional[str] = None
    member_group: Optional[str] = None
    consumer_tax_type: Optional[str] = None

    # Financial summary
    retail_value: float = 0.0
    gross_sales: float = 0.0
    net_sales: float = 0.0
    net_sales_wo_fees: float = 0.0
    delivery_fees: float = 0.0

    # Discounts
    pre_tax_discounts: float = 0.0
    after_tax_discount: float = 0.0
    product_promotions: Optional[str] = None
    cart_promotions: Optional[str] = None
    discount_notes: Optional[str] = None

    # Taxes (detailed)
    pre_al_excise_tax: float = 0.0
    pre_nal_excise_tax: float = 0.0
    city_tax: float = 0.0
    county_tax: float = 0.0
    state_tax: float = 0.0
    federal_tax: float = 0.0
    total_tax: float = 0.0

    # Totals
    total_due: float = 0.0
    tips: float = 0.0
    cogs: float = 0.0

    # Payment
    payment_type: Optional[str] = None
    blazepay_id: Optional[str] = None
    payment_tendered: float = 0.0
    cash_change: float = 0.0
    change_due: float = 0.0

    # Employees
    sold_by_name: Optional[str] = None
    created_by_name: Optional[str] = None
    prepared_by: Optional[str] = None
    packed_by: Optional[str] = None

    # Other
    marketing_source: Optional[str] = None
    order_tags: Optional[str] = None
    loyalty_points_spent: float = 0.0
    loyalty_points_earned: float = 0.0

    # Compliance
    compliance_system: Optional[str] = None
    compliance_order_id: Optional[str] = None

    # Line items
    items: List[ProductSaleResponse] = []
    item_count: int = 0

    class Config:
        from_attributes = True
