-- Migration 003: Create Extended Tables
-- This migration creates all extended tables for the full data overhaul:
-- entities, employee extended, member analytics, extended sales, inventory, sales breakdowns

-- ============================================================
-- ENTITY TABLES
-- ============================================================

-- Vendors table
CREATE TABLE IF NOT EXISTS vendors (
    id VARCHAR(36) PRIMARY KEY,
    vendor_name VARCHAR(500) UNIQUE NOT NULL,
    contact_first_name VARCHAR(255),
    contact_last_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    fax VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    website VARCHAR(500),
    street_address VARCHAR(500),
    city VARCHAR(255),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    description TEXT,
    company_type VARCHAR(100),
    vendor_type VARCHAR(100),
    license_type VARCHAR(100),
    license_number VARCHAR(100)
);
CREATE INDEX IF NOT EXISTS ix_vendors_vendor_name ON vendors(vendor_name);

-- Product Catalog table
CREATE TABLE IF NOT EXISTS product_catalog (
    id VARCHAR(36) PRIMARY KEY,
    shop VARCHAR(255),
    sku VARCHAR(100) UNIQUE NOT NULL,
    item VARCHAR(500),
    category VARCHAR(100),
    cannabis VARCHAR(50),
    measurement VARCHAR(50),
    low_inventory_threshold FLOAT DEFAULT 0.0,
    cost_per_unit FLOAT DEFAULT 0.0,
    wholesale_cost FLOAT DEFAULT 0.0,
    unit_price FLOAT DEFAULT 0.0,
    unit_sale_price FLOAT DEFAULT 0.0,
    half_unit_price FLOAT DEFAULT 0.0,
    half_unit_sale_price FLOAT DEFAULT 0.0,
    two_units_price FLOAT DEFAULT 0.0,
    two_units_sale_price FLOAT DEFAULT 0.0,
    gram_price FLOAT DEFAULT 0.0,
    gram_sale_price FLOAT DEFAULT 0.0,
    eighth_price FLOAT DEFAULT 0.0,
    eighth_sale_price FLOAT DEFAULT 0.0,
    quarter_price FLOAT DEFAULT 0.0,
    quarter_sale_price FLOAT DEFAULT 0.0,
    half_price FLOAT DEFAULT 0.0,
    half_sale_price FLOAT DEFAULT 0.0,
    oz_price FLOAT DEFAULT 0.0,
    oz_sale_price FLOAT DEFAULT 0.0,
    product_type VARCHAR(100),
    description TEXT,
    thc_pct FLOAT DEFAULT 0.0,
    cbd_pct FLOAT DEFAULT 0.0,
    cbn_pct FLOAT DEFAULT 0.0,
    thca_pct FLOAT DEFAULT 0.0,
    cbda_pct FLOAT DEFAULT 0.0,
    cbg_pct FLOAT DEFAULT 0.0,
    thc_mg FLOAT DEFAULT 0.0,
    cbd_mg FLOAT DEFAULT 0.0,
    inventory_available FLOAT DEFAULT 0.0,
    date_purchased DATE,
    vendor_id_ref VARCHAR(100),
    vendor VARCHAR(255),
    genetics VARCHAR(255),
    strain VARCHAR(255),
    product_id VARCHAR(100),
    brand VARCHAR(255),
    cannabis_type VARCHAR(50),
    weight_per_unit FLOAT DEFAULT 0.0,
    active BOOLEAN DEFAULT TRUE,
    available_online BOOLEAN DEFAULT FALSE,
    sell_type VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS ix_product_catalog_sku ON product_catalog(sku);
CREATE INDEX IF NOT EXISTS ix_product_catalog_category ON product_catalog(category);
CREATE INDEX IF NOT EXISTS ix_product_catalog_vendor ON product_catalog(vendor);
CREATE INDEX IF NOT EXISTS ix_product_catalog_brand ON product_catalog(brand);
CREATE INDEX IF NOT EXISTS ix_product_catalog_category_brand ON product_catalog(category, brand);

-- Product Batches table
CREATE TABLE IF NOT EXISTS product_batches (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    shop_name VARCHAR(255),
    vendor_name VARCHAR(255),
    po_number VARCHAR(100),
    batch_description VARCHAR(500),
    brand VARCHAR(255),
    product_id VARCHAR(100),
    product_name VARCHAR(500),
    product_sku VARCHAR(100),
    category VARCHAR(100),
    measurement_type VARCHAR(50),
    weight_type VARCHAR(50),
    weight FLOAT DEFAULT 0.0,
    net_weight FLOAT DEFAULT 0.0,
    status VARCHAR(50),
    archived BOOLEAN DEFAULT FALSE,
    cannabis_type VARCHAR(50),
    batch_id VARCHAR(100),
    metrc_package_label VARCHAR(100),
    purchased_qty FLOAT DEFAULT 0.0,
    current_qty FLOAT DEFAULT 0.0,
    purchased_cost FLOAT DEFAULT 0.0,
    cost_per_unit FLOAT DEFAULT 0.0,
    current_cogs FLOAT DEFAULT 0.0,
    purchased_date DATE,
    sell_by_date DATE,
    expiration_date DATE,
    received_date DATE,
    total_thc_pct FLOAT DEFAULT 0.0,
    total_cbd_pct FLOAT DEFAULT 0.0,
    cbn_pct FLOAT DEFAULT 0.0,
    thca_pct FLOAT DEFAULT 0.0,
    cbda_pct FLOAT DEFAULT 0.0,
    cbg_pct FLOAT DEFAULT 0.0,
    total_terpenes FLOAT DEFAULT 0.0,
    unit_excise_tax FLOAT DEFAULT 0.0,
    total_excise_tax FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_product_batches_line_hash ON product_batches(line_hash);
CREATE INDEX IF NOT EXISTS ix_product_batches_product_sku ON product_batches(product_sku);
CREATE INDEX IF NOT EXISTS ix_product_batches_category ON product_batches(category);
CREATE INDEX IF NOT EXISTS ix_product_batches_batch_id ON product_batches(batch_id);
CREATE INDEX IF NOT EXISTS ix_product_batches_received_date ON product_batches(received_date);
CREATE INDEX IF NOT EXISTS ix_product_batches_sku_batch ON product_batches(product_sku, batch_id);

-- Consumers table
CREATE TABLE IF NOT EXISTS consumers (
    id VARCHAR(36) PRIMARY KEY,
    blaze_consumer_id VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    status VARCHAR(50),
    email VARCHAR(255),
    date_of_birth DATE,
    gender VARCHAR(20),
    date_joined TIMESTAMP,
    is_medical BOOLEAN DEFAULT FALSE,
    phone VARCHAR(50),
    street_address1 VARCHAR(500),
    street_address2 VARCHAR(500),
    city VARCHAR(255),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    country VARCHAR(100),
    dl_number VARCHAR(100),
    dl_state VARCHAR(100),
    dl_expiration DATE,
    rec_number VARCHAR(500),
    rec_expiration DATE,
    rec_issue_date DATE,
    marketing_source VARCHAR(255),
    text_opt_in BOOLEAN DEFAULT FALSE,
    email_opt_in BOOLEAN DEFAULT FALSE,
    consumer_type VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS ix_consumers_blaze_consumer_id ON consumers(blaze_consumer_id);
CREATE INDEX IF NOT EXISTS ix_consumers_date_joined ON consumers(date_joined);
CREATE INDEX IF NOT EXISTS ix_consumers_name ON consumers(first_name, last_name);

-- ============================================================
-- EMPLOYEE EXTENDED TABLES
-- ============================================================

-- Employee Performance table
CREATE TABLE IF NOT EXISTS employee_performance (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE NOT NULL,
    employee_name VARCHAR(255),
    gross_receipts FLOAT DEFAULT 0.0,
    transaction_count INTEGER DEFAULT 0,
    avg_transaction FLOAT DEFAULT 0.0,
    avg_transaction_time VARCHAR(50),
    promotions FLOAT DEFAULT 0.0,
    discounts FLOAT DEFAULT 0.0,
    cash_tendered FLOAT DEFAULT 0.0,
    credit_tendered FLOAT DEFAULT 0.0,
    blazepay_tendered FLOAT DEFAULT 0.0,
    ach_tendered FLOAT DEFAULT 0.0,
    cashless_atm_tendered FLOAT DEFAULT 0.0,
    tips FLOAT DEFAULT 0.0,
    cogs FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_employee_performance_line_hash ON employee_performance(line_hash);
CREATE INDEX IF NOT EXISTS ix_employee_performance_date ON employee_performance(date);
CREATE INDEX IF NOT EXISTS ix_employee_performance_employee_name ON employee_performance(employee_name);
CREATE INDEX IF NOT EXISTS ix_employee_perf_date_emp ON employee_performance(date, employee_name);

-- Employee Activity table
CREATE TABLE IF NOT EXISTS employee_activity (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    time TIMESTAMP,
    employee VARCHAR(255),
    action VARCHAR(255),
    category VARCHAR(255),
    terminal VARCHAR(100)
);
CREATE INDEX IF NOT EXISTS ix_employee_activity_line_hash ON employee_activity(line_hash);
CREATE INDEX IF NOT EXISTS ix_employee_activity_time ON employee_activity(time);
CREATE INDEX IF NOT EXISTS ix_employee_activity_employee ON employee_activity(employee);
CREATE INDEX IF NOT EXISTS ix_employee_activity_action ON employee_activity(action);
CREATE INDEX IF NOT EXISTS ix_employee_activity_time_emp ON employee_activity(time, employee);

-- Time Clock table
CREATE TABLE IF NOT EXISTS time_clock (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE NOT NULL,
    employee VARCHAR(255),
    clock_in TIMESTAMP,
    terminal_in VARCHAR(100),
    clock_out TIMESTAMP,
    terminal_out VARCHAR(100),
    time_clocked_in VARCHAR(50),
    ipad_sessions INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_time_clock_line_hash ON time_clock(line_hash);
CREATE INDEX IF NOT EXISTS ix_time_clock_date ON time_clock(date);
CREATE INDEX IF NOT EXISTS ix_time_clock_employee ON time_clock(employee);
CREATE INDEX IF NOT EXISTS ix_time_clock_date_emp ON time_clock(date, employee);

-- ============================================================
-- MEMBER ANALYTICS TABLES
-- ============================================================

-- Member Performance table
CREATE TABLE IF NOT EXISTS member_performance (
    id VARCHAR(36) PRIMARY KEY,
    member_id VARCHAR(100) UNIQUE NOT NULL,
    member_name VARCHAR(255),
    member_phone VARCHAR(50),
    marketing_src VARCHAR(255),
    member_group VARCHAR(100),
    date_joined TIMESTAMP,
    consumer_type VARCHAR(50),
    loyalty_points FLOAT DEFAULT 0.0,
    state VARCHAR(100),
    zip_code VARCHAR(20),
    last_visited TIMESTAMP,
    num_visits INTEGER DEFAULT 0,
    num_sales INTEGER DEFAULT 0,
    num_refunds INTEGER DEFAULT 0,
    gross_sales_receipts FLOAT DEFAULT 0.0,
    gross_refund_receipts FLOAT DEFAULT 0.0,
    avg_sales_receipts FLOAT DEFAULT 0.0,
    avg_refund_receipts FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_member_performance_member_id ON member_performance(member_id);

-- Inactive Members table
CREATE TABLE IF NOT EXISTS inactive_members (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    cell_phone VARCHAR(50),
    email VARCHAR(255),
    last_visit TIMESTAMP,
    rec_exp_date DATE,
    total_amount_spent FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_inactive_members_line_hash ON inactive_members(line_hash);
CREATE INDEX IF NOT EXISTS ix_inactive_members_last_visit ON inactive_members(last_visit);
CREATE INDEX IF NOT EXISTS ix_inactive_members_name ON inactive_members(first_name, last_name);

-- Marketing Contacts table
CREATE TABLE IF NOT EXISTS marketing_contacts (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    membership_group VARCHAR(100),
    marketing_source VARCHAR(255),
    email VARCHAR(255),
    loyalty_points FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_marketing_contacts_line_hash ON marketing_contacts(line_hash);
CREATE INDEX IF NOT EXISTS ix_marketing_contacts_name ON marketing_contacts(first_name, last_name);

-- ============================================================
-- EXTENDED SALES & FINANCIAL TABLES
-- ============================================================

-- Delivery Sales table
CREATE TABLE IF NOT EXISTS delivery_sales (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date TIMESTAMP,
    transaction_id VARCHAR(100),
    metrc_id VARCHAR(100),
    metrc_delivery_id VARCHAR(100),
    customer_first_name VARCHAR(255),
    customer_last_name VARCHAR(255),
    dob DATE,
    delivery_address VARCHAR(500),
    city VARCHAR(255),
    zip_code VARCHAR(20),
    region VARCHAR(100),
    employee VARCHAR(255),
    order_source VARCHAR(100),
    sales FLOAT DEFAULT 0.0,
    discounts FLOAT DEFAULT 0.0,
    subtotal FLOAT DEFAULT 0.0,
    fees FLOAT DEFAULT 0.0,
    al_excise FLOAT DEFAULT 0.0,
    nal_excise FLOAT DEFAULT 0.0,
    ohio_excise_tax FLOAT DEFAULT 0.0,
    county_tax FLOAT DEFAULT 0.0,
    state_tax FLOAT DEFAULT 0.0,
    state_excise_tax FLOAT DEFAULT 0.0,
    gross_receipts FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_delivery_sales_line_hash ON delivery_sales(line_hash);
CREATE INDEX IF NOT EXISTS ix_delivery_sales_date ON delivery_sales(date);
CREATE INDEX IF NOT EXISTS ix_delivery_sales_transaction_id ON delivery_sales(transaction_id);

-- Canceled/Void Sales table
CREATE TABLE IF NOT EXISTS canceled_void_sales (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date TIMESTAMP,
    member VARCHAR(255),
    transaction_no VARCHAR(50),
    trans_type VARCHAR(50),
    trans_status VARCHAR(50),
    queue_type VARCHAR(50),
    member_id VARCHAR(100),
    cancellation_reason TEXT,
    consumer_tax_type VARCHAR(50),
    cogs FLOAT DEFAULT 0.0,
    retail_value FLOAT DEFAULT 0.0,
    discounts FLOAT DEFAULT 0.0,
    net_sales FLOAT DEFAULT 0.0,
    total_tax FLOAT DEFAULT 0.0,
    delivery_fees FLOAT DEFAULT 0.0,
    tips FLOAT DEFAULT 0.0,
    after_tax_discount FLOAT DEFAULT 0.0,
    gross_receipt FLOAT DEFAULT 0.0,
    employee VARCHAR(255),
    terminal VARCHAR(100),
    payment_type VARCHAR(50),
    promotions TEXT,
    marketing_source VARCHAR(255),
    gross_sales FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_canceled_void_sales_line_hash ON canceled_void_sales(line_hash);
CREATE INDEX IF NOT EXISTS ix_canceled_void_sales_date ON canceled_void_sales(date);
CREATE INDEX IF NOT EXISTS ix_canceled_void_sales_transaction_no ON canceled_void_sales(transaction_no);

-- Uncomplete Sales table
CREATE TABLE IF NOT EXISTS uncomplete_sales (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date TIMESTAMP,
    member VARCHAR(255),
    transaction_no VARCHAR(50),
    trans_type VARCHAR(50),
    trans_status VARCHAR(50),
    consumer_tax_type VARCHAR(50),
    cogs FLOAT DEFAULT 0.0,
    retail_value FLOAT DEFAULT 0.0,
    discounts FLOAT DEFAULT 0.0,
    total_tax FLOAT DEFAULT 0.0,
    delivery_fees FLOAT DEFAULT 0.0,
    tips FLOAT DEFAULT 0.0,
    after_tax_discount FLOAT DEFAULT 0.0,
    gross_receipt FLOAT DEFAULT 0.0,
    employee VARCHAR(255),
    terminal VARCHAR(100),
    payment_type VARCHAR(50),
    promotions TEXT,
    marketing_source VARCHAR(255),
    metrc_id VARCHAR(100)
);
CREATE INDEX IF NOT EXISTS ix_uncomplete_sales_line_hash ON uncomplete_sales(line_hash);
CREATE INDEX IF NOT EXISTS ix_uncomplete_sales_date ON uncomplete_sales(date);
CREATE INDEX IF NOT EXISTS ix_uncomplete_sales_transaction_no ON uncomplete_sales(transaction_no);

-- Promotions Activity table
CREATE TABLE IF NOT EXISTS promotions_activity (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date TIMESTAMP,
    transaction_no VARCHAR(50),
    reward_system VARCHAR(100),
    promo_name VARCHAR(500),
    promo_type VARCHAR(100),
    code_used VARCHAR(100),
    cash_value FLOAT DEFAULT 0.0,
    employee VARCHAR(255),
    member VARCHAR(255)
);
CREATE INDEX IF NOT EXISTS ix_promotions_activity_line_hash ON promotions_activity(line_hash);
CREATE INDEX IF NOT EXISTS ix_promotions_activity_date ON promotions_activity(date);
CREATE INDEX IF NOT EXISTS ix_promotions_activity_transaction_no ON promotions_activity(transaction_no);

-- Profit/Loss table
CREATE TABLE IF NOT EXISTS profit_loss (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE NOT NULL,
    gross_receipts FLOAT DEFAULT 0.0,
    cost FLOAT DEFAULT 0.0,
    loss FLOAT DEFAULT 0.0,
    profit FLOAT DEFAULT 0.0,
    discount FLOAT DEFAULT 0.0,
    margin_pct FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_profit_loss_line_hash ON profit_loss(line_hash);
CREATE INDEX IF NOT EXISTS ix_profit_loss_date ON profit_loss(date);

-- Purchase Order by Category table
CREATE TABLE IF NOT EXISTS purchase_order_by_category (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    po_date DATE,
    vendor_name VARCHAR(255),
    product_category VARCHAR(100),
    cogs FLOAT DEFAULT 0.0,
    excise_tax FLOAT DEFAULT 0.0,
    po_number VARCHAR(100)
);
CREATE INDEX IF NOT EXISTS ix_purchase_order_by_category_line_hash ON purchase_order_by_category(line_hash);
CREATE INDEX IF NOT EXISTS ix_purchase_order_by_category_po_date ON purchase_order_by_category(po_date);
CREATE INDEX IF NOT EXISTS ix_purchase_order_by_category_vendor_name ON purchase_order_by_category(vendor_name);

-- Return to Vendor table
CREATE TABLE IF NOT EXISTS return_to_vendor (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE,
    vendor VARCHAR(255),
    product_category VARCHAR(100),
    product VARCHAR(500),
    low_inventory_threshold FLOAT DEFAULT 0.0,
    batch_sku VARCHAR(100),
    quantity FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_return_to_vendor_line_hash ON return_to_vendor(line_hash);
CREATE INDEX IF NOT EXISTS ix_return_to_vendor_date ON return_to_vendor(date);

-- Refund History Detail table
CREATE TABLE IF NOT EXISTS refund_history_detail (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE NOT NULL,
    transaction_no VARCHAR(50),
    employee VARCHAR(255),
    customer VARCHAR(255),
    with_inventory BOOLEAN DEFAULT FALSE,
    refund_as VARCHAR(50),
    refund_amount FLOAT DEFAULT 0.0,
    product VARCHAR(500),
    quantity FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_refund_history_detail_line_hash ON refund_history_detail(line_hash);
CREATE INDEX IF NOT EXISTS ix_refund_history_detail_date ON refund_history_detail(date);
CREATE INDEX IF NOT EXISTS ix_refund_history_detail_transaction_no ON refund_history_detail(transaction_no);

-- Paid In/Out Activity table
CREATE TABLE IF NOT EXISTS paidinout_activity (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE,
    cash_drawer_date DATE,
    employee VARCHAR(255),
    terminal VARCHAR(100),
    starting_cash FLOAT DEFAULT 0.0,
    day_end FLOAT DEFAULT 0.0,
    daily_sales FLOAT DEFAULT 0.0,
    paid_in FLOAT DEFAULT 0.0,
    paid_out FLOAT DEFAULT 0.0,
    cash_drop FLOAT DEFAULT 0.0,
    notes TEXT
);
CREATE INDEX IF NOT EXISTS ix_paidinout_activity_line_hash ON paidinout_activity(line_hash);
CREATE INDEX IF NOT EXISTS ix_paidinout_activity_date ON paidinout_activity(date);

-- ============================================================
-- EXTENDED INVENTORY TABLES
-- ============================================================

-- Inventory Aging table
CREATE TABLE IF NOT EXISTS inventory_aging (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    product_sku VARCHAR(100),
    product_name VARCHAR(500),
    product_category VARCHAR(100),
    low_inventory_threshold FLOAT DEFAULT 0.0,
    days_0_30_qty FLOAT DEFAULT 0.0,
    days_0_30_val FLOAT DEFAULT 0.0,
    days_31_45_qty FLOAT DEFAULT 0.0,
    days_31_45_val FLOAT DEFAULT 0.0,
    days_46_60_qty FLOAT DEFAULT 0.0,
    days_46_60_val FLOAT DEFAULT 0.0,
    days_61_90_qty FLOAT DEFAULT 0.0,
    days_61_90_val FLOAT DEFAULT 0.0,
    days_90_plus_qty FLOAT DEFAULT 0.0,
    days_90_plus_val FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_inventory_aging_line_hash ON inventory_aging(line_hash);
CREATE INDEX IF NOT EXISTS ix_inventory_aging_product_sku ON inventory_aging(product_sku);

-- Inventory Distribution table
CREATE TABLE IF NOT EXISTS inventory_distribution (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    product VARCHAR(500),
    category VARCHAR(100),
    brand VARCHAR(255),
    unit_type VARCHAR(50),
    low_inventory_threshold FLOAT DEFAULT 0.0,
    total FLOAT DEFAULT 0.0,
    exchange FLOAT DEFAULT 0.0,
    fulfillment FLOAT DEFAULT 0.0,
    quarantine FLOAT DEFAULT 0.0,
    safe FLOAT DEFAULT 0.0,
    vault FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_inventory_distribution_line_hash ON inventory_distribution(line_hash);
CREATE INDEX IF NOT EXISTS ix_inventory_distribution_category ON inventory_distribution(category);

-- Inventory Valuation table
CREATE TABLE IF NOT EXISTS inventory_valuation (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    product_name VARCHAR(500),
    category VARCHAR(100),
    cannabis_type VARCHAR(50),
    status VARCHAR(50),
    avg_unit_cost FLOAT DEFAULT 0.0,
    avg_excise_cost FLOAT DEFAULT 0.0,
    unit_excise_cost FLOAT DEFAULT 0.0,
    avg_retail_price FLOAT DEFAULT 0.0,
    avg_profit FLOAT DEFAULT 0.0,
    avg_margin_pct FLOAT DEFAULT 0.0,
    avg_markup_pct FLOAT DEFAULT 0.0,
    total_available_qty FLOAT DEFAULT 0.0,
    total_available_cogs FLOAT DEFAULT 0.0,
    total_available_excise FLOAT DEFAULT 0.0,
    total_available_cogs_excise FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_inventory_valuation_line_hash ON inventory_valuation(line_hash);
CREATE INDEX IF NOT EXISTS ix_inventory_valuation_category ON inventory_valuation(category);

-- Inventory Transfers table
CREATE TABLE IF NOT EXISTS inventory_transfers (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date TIMESTAMP,
    employee VARCHAR(255),
    product VARCHAR(500),
    origin_shop VARCHAR(255),
    origin_inventory VARCHAR(255),
    destination_shop VARCHAR(255),
    destination VARCHAR(255),
    amount FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_inventory_transfers_line_hash ON inventory_transfers(line_hash);
CREATE INDEX IF NOT EXISTS ix_inventory_transfers_date ON inventory_transfers(date);

-- Sell Through table
CREATE TABLE IF NOT EXISTS sell_through (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    product_id VARCHAR(100),
    product_name VARCHAR(500),
    category VARCHAR(100),
    low_inventory_threshold FLOAT DEFAULT 0.0,
    avg_qty_sold_per_day FLOAT DEFAULT 0.0,
    days_remaining FLOAT DEFAULT 0.0,
    qty_on_hand FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_sell_through_line_hash ON sell_through(line_hash);
CREATE INDEX IF NOT EXISTS ix_sell_through_product_id ON sell_through(product_id);

-- Current Inventory table
CREATE TABLE IF NOT EXISTS current_inventory (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    product VARCHAR(500),
    category VARCHAR(100),
    status VARCHAR(50),
    low_inventory_threshold FLOAT DEFAULT 0.0,
    current_quantity FLOAT DEFAULT 0.0,
    current_cogs FLOAT DEFAULT 0.0,
    sold_quantity FLOAT DEFAULT 0.0,
    sold_cogs FLOAT DEFAULT 0.0,
    current_prepackages FLOAT DEFAULT 0.0,
    current_pack_cogs FLOAT DEFAULT 0.0,
    sold_prepackages FLOAT DEFAULT 0.0,
    sold_pack_cogs FLOAT DEFAULT 0.0,
    retail_price FLOAT DEFAULT 0.0,
    retail_value FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_current_inventory_line_hash ON current_inventory(line_hash);
CREATE INDEX IF NOT EXISTS ix_current_inventory_category ON current_inventory(category);

-- ============================================================
-- SALES BREAKDOWN TABLES
-- ============================================================

-- Sales by City table
CREATE TABLE IF NOT EXISTS sales_by_city (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    city VARCHAR(255),
    state VARCHAR(100),
    transactions INTEGER DEFAULT 0,
    subtotal_sales FLOAT DEFAULT 0.0,
    discount FLOAT DEFAULT 0.0,
    total_taxes FLOAT DEFAULT 0.0,
    delivery_fee FLOAT DEFAULT 0.0,
    tips FLOAT DEFAULT 0.0,
    gross_receipts FLOAT DEFAULT 0.0,
    percentage_of_sales FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_sales_by_city_line_hash ON sales_by_city(line_hash);
CREATE INDEX IF NOT EXISTS ix_sales_by_city_city ON sales_by_city(city);

-- Sales by Hour table
CREATE TABLE IF NOT EXISTS sales_by_hour (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    hour VARCHAR(20),
    recreational_sales FLOAT DEFAULT 0.0,
    medical_sales FLOAT DEFAULT 0.0,
    total_sales FLOAT DEFAULT 0.0,
    recreational_discounts FLOAT DEFAULT 0.0,
    medicinal_discounts FLOAT DEFAULT 0.0,
    total_discounts FLOAT DEFAULT 0.0,
    gross_receipts FLOAT DEFAULT 0.0,
    num_transactions INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_sales_by_hour_line_hash ON sales_by_hour(line_hash);

-- Sales by Product table
CREATE TABLE IF NOT EXISTS sales_by_product (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    product VARCHAR(500),
    sku VARCHAR(100),
    category VARCHAR(100),
    vendor VARCHAR(255),
    brand VARCHAR(255),
    product_tags TEXT,
    units_sold FLOAT DEFAULT 0.0,
    cogs FLOAT DEFAULT 0.0,
    retail_value FLOAT DEFAULT 0.0,
    total_discounts FLOAT DEFAULT 0.0,
    product_discounts FLOAT DEFAULT 0.0,
    cart_discounts FLOAT DEFAULT 0.0,
    net_sales FLOAT DEFAULT 0.0,
    subtotal_sales FLOAT DEFAULT 0.0,
    total_tax FLOAT DEFAULT 0.0,
    delivery_fees FLOAT DEFAULT 0.0,
    after_tax_discounts FLOAT DEFAULT 0.0,
    margin FLOAT DEFAULT 0.0,
    revenue_per_unit FLOAT DEFAULT 0.0,
    pct_of_sales FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_sales_by_product_line_hash ON sales_by_product(line_hash);
CREATE INDEX IF NOT EXISTS ix_sales_by_product_sku ON sales_by_product(sku);
CREATE INDEX IF NOT EXISTS ix_sales_by_product_category ON sales_by_product(category);

-- Sales by Product Category table
CREATE TABLE IF NOT EXISTS sales_by_product_category (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    product_category VARCHAR(100),
    num_trans INTEGER DEFAULT 0,
    cogs FLOAT DEFAULT 0.0,
    retail_value FLOAT DEFAULT 0.0,
    total_discounts FLOAT DEFAULT 0.0,
    product_discounts FLOAT DEFAULT 0.0,
    subtotal_sales FLOAT DEFAULT 0.0,
    cart_discounts FLOAT DEFAULT 0.0,
    net_sales FLOAT DEFAULT 0.0,
    total_tax FLOAT DEFAULT 0.0,
    delivery_fees FLOAT DEFAULT 0.0,
    after_tax_discounts FLOAT DEFAULT 0.0,
    gross_receipt FLOAT DEFAULT 0.0,
    units_sold FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_sales_by_product_category_line_hash ON sales_by_product_category(line_hash);
CREATE INDEX IF NOT EXISTS ix_sales_by_product_category_cat ON sales_by_product_category(product_category);

-- Sales by Vendor table
CREATE TABLE IF NOT EXISTS sales_by_vendor (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    vendor VARCHAR(255),
    transaction_type VARCHAR(50),
    subtotal_sales FLOAT DEFAULT 0.0,
    delivery_fees FLOAT DEFAULT 0.0,
    discounts FLOAT DEFAULT 0.0,
    after_tax_discount FLOAT DEFAULT 0.0,
    tax FLOAT DEFAULT 0.0,
    gross_receipt FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_sales_by_vendor_line_hash ON sales_by_vendor(line_hash);
CREATE INDEX IF NOT EXISTS ix_sales_by_vendor_vendor ON sales_by_vendor(vendor);

-- Sales by Consumer Type table
CREATE TABLE IF NOT EXISTS sales_by_consumer_type (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    breakdown VARCHAR(100),
    cannabis_retail_value FLOAT DEFAULT 0.0,
    non_cannabis_retail_value FLOAT DEFAULT 0.0,
    cannabis_discounts FLOAT DEFAULT 0.0,
    non_cannabis_discounts FLOAT DEFAULT 0.0,
    total_discounts FLOAT DEFAULT 0.0,
    after_tax_discount FLOAT DEFAULT 0.0,
    gross_revenue FLOAT DEFAULT 0.0,
    total_tax FLOAT DEFAULT 0.0,
    delivery_fees FLOAT DEFAULT 0.0,
    tips FLOAT DEFAULT 0.0,
    gross_receipt FLOAT DEFAULT 0.0,
    cogs FLOAT DEFAULT 0.0,
    net_profit FLOAT DEFAULT 0.0,
    num_visits INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_sales_by_consumer_type_line_hash ON sales_by_consumer_type(line_hash);

-- Employee Sales by Product table
CREATE TABLE IF NOT EXISTS employee_sales_by_product (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    product VARCHAR(500),
    employee VARCHAR(255),
    quantity FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_employee_sales_by_product_line_hash ON employee_sales_by_product(line_hash);
CREATE INDEX IF NOT EXISTS ix_employee_sales_by_product_employee ON employee_sales_by_product(employee);

-- Products by Vendor table
CREATE TABLE IF NOT EXISTS products_by_vendor (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    vendor VARCHAR(255),
    contact_first_name VARCHAR(255),
    contact_surname VARCHAR(255),
    category VARCHAR(100),
    brand VARCHAR(255),
    product VARCHAR(500),
    quantity_sold FLOAT DEFAULT 0.0,
    quantity_in_stock FLOAT DEFAULT 0.0,
    sales FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_products_by_vendor_line_hash ON products_by_vendor(line_hash);
CREATE INDEX IF NOT EXISTS ix_products_by_vendor_vendor ON products_by_vendor(vendor);

-- Product Sales by Inventory table
CREATE TABLE IF NOT EXISTS product_sales_by_inventory (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    product VARCHAR(500),
    sku VARCHAR(100),
    category VARCHAR(100),
    vendor VARCHAR(255),
    brand VARCHAR(255),
    product_tags TEXT,
    total_units_sold FLOAT DEFAULT 0.0,
    quarantine_units_sold FLOAT DEFAULT 0.0,
    vault_units_sold FLOAT DEFAULT 0.0,
    fulfillment_units_sold FLOAT DEFAULT 0.0,
    exchange_units_sold FLOAT DEFAULT 0.0,
    sales_floor_units_sold FLOAT DEFAULT 0.0,
    safe_units_sold FLOAT DEFAULT 0.0,
    delivery_units_sold FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_product_sales_by_inventory_line_hash ON product_sales_by_inventory(line_hash);
CREATE INDEX IF NOT EXISTS ix_product_sales_by_inventory_sku ON product_sales_by_inventory(sku);

-- Product Sell By / Expire table
CREATE TABLE IF NOT EXISTS product_sell_by_expire (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    product_category VARCHAR(100),
    product_name VARCHAR(500),
    status VARCHAR(50),
    batch_id VARCHAR(100),
    sell_by_date DATE,
    qty_remaining FLOAT DEFAULT 0.0,
    low_inventory_threshold FLOAT DEFAULT 0.0,
    unit_type VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS ix_product_sell_by_expire_line_hash ON product_sell_by_expire(line_hash);
CREATE INDEX IF NOT EXISTS ix_product_sell_by_expire_category ON product_sell_by_expire(product_category);
CREATE INDEX IF NOT EXISTS ix_product_sell_by_expire_sell_by_date ON product_sell_by_expire(sell_by_date);

-- Log migration completion
SELECT 'Migration 003_create_extended_tables completed successfully' AS status;
