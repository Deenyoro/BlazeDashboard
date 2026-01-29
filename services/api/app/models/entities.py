"""
Master data models: Vendors, Product Catalog, Product Batches, Consumers.
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, Date, DateTime, Index
from app.core.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class Vendor(Base):
    """Vendor directory from vendors_export.csv."""
    __tablename__ = "vendors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    vendor_name = Column(String(500), unique=True, nullable=False, index=True)
    contact_first_name = Column(String(255), nullable=True)
    contact_last_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    fax = Column(String(50), nullable=True)
    active = Column(Boolean, default=True)
    website = Column(String(500), nullable=True)
    street_address = Column(String(500), nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    company_type = Column(String(100), nullable=True)
    vendor_type = Column(String(100), nullable=True)
    license_type = Column(String(100), nullable=True)
    license_number = Column(String(100), nullable=True)


class ProductCatalog(Base):
    """Product catalog from company_products_export.csv."""
    __tablename__ = "product_catalog"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    shop = Column(String(255), nullable=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    item = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    cannabis = Column(String(50), nullable=True)
    measurement = Column(String(50), nullable=True)
    low_inventory_threshold = Column(Float, default=0.0)
    cost_per_unit = Column(Float, default=0.0)
    wholesale_cost = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)
    unit_sale_price = Column(Float, default=0.0)
    half_unit_price = Column(Float, default=0.0)
    half_unit_sale_price = Column(Float, default=0.0)
    two_units_price = Column(Float, default=0.0)
    two_units_sale_price = Column(Float, default=0.0)
    gram_price = Column(Float, default=0.0)
    gram_sale_price = Column(Float, default=0.0)
    eighth_price = Column(Float, default=0.0)
    eighth_sale_price = Column(Float, default=0.0)
    quarter_price = Column(Float, default=0.0)
    quarter_sale_price = Column(Float, default=0.0)
    half_price = Column(Float, default=0.0)
    half_sale_price = Column(Float, default=0.0)
    oz_price = Column(Float, default=0.0)
    oz_sale_price = Column(Float, default=0.0)
    product_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    thc_pct = Column(Float, default=0.0)
    cbd_pct = Column(Float, default=0.0)
    cbn_pct = Column(Float, default=0.0)
    thca_pct = Column(Float, default=0.0)
    cbda_pct = Column(Float, default=0.0)
    cbg_pct = Column(Float, default=0.0)
    thc_mg = Column(Float, default=0.0)
    cbd_mg = Column(Float, default=0.0)
    inventory_available = Column(Float, default=0.0)
    date_purchased = Column(Date, nullable=True)
    vendor_id_ref = Column(String(100), nullable=True)
    vendor = Column(String(255), nullable=True, index=True)
    genetics = Column(String(255), nullable=True)
    strain = Column(String(255), nullable=True)
    product_id = Column(String(100), nullable=True)
    brand = Column(String(255), nullable=True, index=True)
    cannabis_type = Column(String(50), nullable=True)
    weight_per_unit = Column(Float, default=0.0)
    active = Column(Boolean, default=True)
    available_online = Column(Boolean, default=False)
    sell_type = Column(String(50), nullable=True)

    __table_args__ = (
        Index('ix_product_catalog_category_brand', 'category', 'brand'),
    )


class ProductBatch(Base):
    """Product batch data from company_product_batch_export.csv."""
    __tablename__ = "product_batches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_hash = Column(String(64), unique=True, nullable=False, index=True)

    shop_name = Column(String(255), nullable=True)
    vendor_name = Column(String(255), nullable=True)
    po_number = Column(String(100), nullable=True)
    batch_description = Column(String(500), nullable=True)
    brand = Column(String(255), nullable=True)
    product_id = Column(String(100), nullable=True)
    product_name = Column(String(500), nullable=True)
    product_sku = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    measurement_type = Column(String(50), nullable=True)
    weight_type = Column(String(50), nullable=True)
    weight = Column(Float, default=0.0)
    net_weight = Column(Float, default=0.0)
    status = Column(String(50), nullable=True)
    archived = Column(Boolean, default=False)
    cannabis_type = Column(String(50), nullable=True)
    batch_id = Column(String(100), nullable=True, index=True)
    metrc_package_label = Column(String(100), nullable=True)
    purchased_qty = Column(Float, default=0.0)
    current_qty = Column(Float, default=0.0)
    purchased_cost = Column(Float, default=0.0)
    cost_per_unit = Column(Float, default=0.0)
    current_cogs = Column(Float, default=0.0)
    purchased_date = Column(Date, nullable=True)
    sell_by_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    received_date = Column(Date, nullable=True, index=True)
    total_thc_pct = Column(Float, default=0.0)
    total_cbd_pct = Column(Float, default=0.0)
    cbn_pct = Column(Float, default=0.0)
    thca_pct = Column(Float, default=0.0)
    cbda_pct = Column(Float, default=0.0)
    cbg_pct = Column(Float, default=0.0)
    total_terpenes = Column(Float, default=0.0)
    unit_excise_tax = Column(Float, default=0.0)
    total_excise_tax = Column(Float, default=0.0)

    __table_args__ = (
        Index('ix_product_batches_sku_batch', 'product_sku', 'batch_id'),
    )


class Consumer(Base):
    """Consumer/customer data from consumer_export.csv."""
    __tablename__ = "consumers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    blaze_consumer_id = Column(String(100), unique=True, nullable=False, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    date_joined = Column(DateTime, nullable=True, index=True)
    is_medical = Column(Boolean, default=False)
    phone = Column(String(50), nullable=True)
    street_address1 = Column(String(500), nullable=True)
    street_address2 = Column(String(500), nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    dl_number = Column(String(100), nullable=True)
    dl_state = Column(String(100), nullable=True)
    dl_expiration = Column(Date, nullable=True)
    rec_number = Column(String(500), nullable=True)
    rec_expiration = Column(Date, nullable=True)
    rec_issue_date = Column(Date, nullable=True)
    marketing_source = Column(String(255), nullable=True)
    text_opt_in = Column(Boolean, default=False)
    email_opt_in = Column(Boolean, default=False)
    consumer_type = Column(String(50), nullable=True)

    __table_args__ = (
        Index('ix_consumers_name', 'first_name', 'last_name'),
    )
