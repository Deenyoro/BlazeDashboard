-- Migration 002: Create Report Tables
-- This migration creates all the additional report tables for comprehensive Blaze data ingestion

-- Refund History table
CREATE TABLE IF NOT EXISTS refund_history (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE NOT NULL,
    trans_no VARCHAR(50) NOT NULL,
    employee VARCHAR(255),
    customer VARCHAR(255),
    with_inventory BOOLEAN DEFAULT FALSE,
    product VARCHAR(500),
    refund_as VARCHAR(50),
    item_price FLOAT DEFAULT 0.0,
    refund_amount FLOAT DEFAULT 0.0,
    quantity FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_refund_history_line_hash ON refund_history(line_hash);
CREATE INDEX IF NOT EXISTS ix_refund_history_date ON refund_history(date);
CREATE INDEX IF NOT EXISTS ix_refund_history_trans_no ON refund_history(trans_no);
CREATE INDEX IF NOT EXISTS ix_refund_history_date_trans ON refund_history(date, trans_no);

-- Sales Payments table
CREATE TABLE IF NOT EXISTS sales_payments (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    trans_no VARCHAR(50) NOT NULL,
    trans_status VARCHAR(50),
    date DATE NOT NULL,
    company VARCHAR(500),
    shop VARCHAR(255),
    payment_type VARCHAR(50),
    amount_due FLOAT DEFAULT 0.0,
    cash_back FLOAT DEFAULT 0.0,
    tips FLOAT DEFAULT 0.0,
    change_due FLOAT DEFAULT 0.0,
    payment_tendered FLOAT DEFAULT 0.0,
    payment_fee FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_sales_payments_line_hash ON sales_payments(line_hash);
CREATE INDEX IF NOT EXISTS ix_sales_payments_trans_no ON sales_payments(trans_no);
CREATE INDEX IF NOT EXISTS ix_sales_payments_date ON sales_payments(date);
CREATE INDEX IF NOT EXISTS ix_sales_payments_payment_type ON sales_payments(payment_type);
CREATE INDEX IF NOT EXISTS ix_sales_payments_date_type ON sales_payments(date, payment_type);

-- Sales by Queue table
CREATE TABLE IF NOT EXISTS sales_by_queue (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE NOT NULL,
    shop VARCHAR(255),
    company VARCHAR(500),
    queue_type VARCHAR(50),
    total_due FLOAT DEFAULT 0.0,
    net_sales FLOAT DEFAULT 0.0,
    net_sales_wo_fees FLOAT DEFAULT 0.0,
    num_completed_transactions INTEGER DEFAULT 0,
    num_refunds INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_sales_by_queue_line_hash ON sales_by_queue(line_hash);
CREATE INDEX IF NOT EXISTS ix_sales_by_queue_date ON sales_by_queue(date);
CREATE INDEX IF NOT EXISTS ix_sales_by_queue_queue_type ON sales_by_queue(queue_type);
CREATE INDEX IF NOT EXISTS ix_sales_by_queue_date_shop ON sales_by_queue(date, shop);

-- Received Inventory (Purchase Orders) table
CREATE TABLE IF NOT EXISTS received_inventory (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    company VARCHAR(500),
    shop VARCHAR(255),
    date DATE NOT NULL,
    completed_date DATE,
    delivery_date DATE,
    received_date DATE,
    approved_date DATE,
    po_date DATE,
    po_number VARCHAR(100),
    po_status VARCHAR(50),
    transaction_type VARCHAR(50),
    sb_number VARCHAR(100),
    payment_status VARCHAR(50),
    reference VARCHAR(255),
    unique_id VARCHAR(100),
    product_sku VARCHAR(100),
    product VARCHAR(500),
    brand VARCHAR(255),
    category VARCHAR(100),
    vendor VARCHAR(255),
    metrc_tag VARCHAR(100),
    paid_amount FLOAT DEFAULT 0.0,
    unpaid_amount FLOAT DEFAULT 0.0,
    unit_cost FLOAT DEFAULT 0.0,
    request_quantity FLOAT DEFAULT 0.0,
    received_quantity FLOAT DEFAULT 0.0,
    request_total_cost FLOAT DEFAULT 0.0,
    received_total_cost FLOAT DEFAULT 0.0,
    final_total_cost FLOAT DEFAULT 0.0,
    excise_tax FLOAT DEFAULT 0.0,
    discount FLOAT DEFAULT 0.0,
    adjustment_amount FLOAT DEFAULT 0.0,
    fees FLOAT DEFAULT 0.0,
    grand_total FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_received_inventory_line_hash ON received_inventory(line_hash);
CREATE INDEX IF NOT EXISTS ix_received_inventory_date ON received_inventory(date);
CREATE INDEX IF NOT EXISTS ix_received_inventory_po_number ON received_inventory(po_number);
CREATE INDEX IF NOT EXISTS ix_received_inventory_product_sku ON received_inventory(product_sku);
CREATE INDEX IF NOT EXISTS ix_received_inventory_date_po ON received_inventory(date, po_number);
CREATE INDEX IF NOT EXISTS ix_received_inventory_sku ON received_inventory(product_sku);

-- Inventory Reconciliation table
CREATE TABLE IF NOT EXISTS inventory_reconciliation (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE NOT NULL,
    date_timestamp TIMESTAMP,
    shop VARCHAR(255),
    company VARCHAR(500),
    reconciliation_no VARCHAR(100),
    employee_name VARCHAR(255),
    inventory_name VARCHAR(255),
    product_name VARCHAR(500),
    brand_name VARCHAR(255),
    product_sku VARCHAR(100),
    category_name VARCHAR(100),
    batch_sku VARCHAR(100),
    metrc_tag VARCHAR(100),
    new_quantity FLOAT DEFAULT 0.0,
    old_quantity FLOAT DEFAULT 0.0,
    difference FLOAT DEFAULT 0.0,
    report_loss BOOLEAN DEFAULT FALSE,
    metrc_adjustment VARCHAR(100),
    low_inventory_threshold FLOAT DEFAULT 0.0,
    cost_per_unit FLOAT DEFAULT 0.0,
    cogs FLOAT DEFAULT 0.0,
    pre_package_name VARCHAR(255),
    reason VARCHAR(100),
    reason_note TEXT
);
CREATE INDEX IF NOT EXISTS ix_inventory_reconciliation_line_hash ON inventory_reconciliation(line_hash);
CREATE INDEX IF NOT EXISTS ix_inventory_reconciliation_date ON inventory_reconciliation(date);
CREATE INDEX IF NOT EXISTS ix_inventory_reconciliation_reconciliation_no ON inventory_reconciliation(reconciliation_no);
CREATE INDEX IF NOT EXISTS ix_inventory_reconciliation_product_sku ON inventory_reconciliation(product_sku);
CREATE INDEX IF NOT EXISTS ix_inventory_recon_date_sku ON inventory_reconciliation(date, product_sku);

-- Inventory Actions table
CREATE TABLE IF NOT EXISTS inventory_actions (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE NOT NULL,
    unique_id VARCHAR(100),
    metrc_tag VARCHAR(100),
    product VARCHAR(500),
    category VARCHAR(100),
    source VARCHAR(100),
    action VARCHAR(50),
    quantity FLOAT DEFAULT 0.0,
    inventory_value FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_inventory_actions_line_hash ON inventory_actions(line_hash);
CREATE INDEX IF NOT EXISTS ix_inventory_actions_date ON inventory_actions(date);
CREATE INDEX IF NOT EXISTS ix_inventory_actions_action ON inventory_actions(action);
CREATE INDEX IF NOT EXISTS ix_inventory_actions_date_action ON inventory_actions(date, action);

-- Daily Accounting Summary table
CREATE TABLE IF NOT EXISTS daily_accounting_summary (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE NOT NULL,
    shop VARCHAR(255),
    company VARCHAR(500),
    queue_type VARCHAR(50),
    adult_retail_value FLOAT DEFAULT 0.0,
    medical_retail_value FLOAT DEFAULT 0.0,
    non_cannabis_retail_value FLOAT DEFAULT 0.0,
    retail_value_of_sales FLOAT DEFAULT 0.0,
    pre_al_excise_tax FLOAT DEFAULT 0.0,
    pre_nal_excise_tax FLOAT DEFAULT 0.0,
    pre_city_tax FLOAT DEFAULT 0.0,
    pre_county_tax FLOAT DEFAULT 0.0,
    pre_state_tax FLOAT DEFAULT 0.0,
    pre_federal_tax FLOAT DEFAULT 0.0,
    adult_gross_sales FLOAT DEFAULT 0.0,
    medical_gross_sales FLOAT DEFAULT 0.0,
    non_cannabis_gross_sales FLOAT DEFAULT 0.0,
    gross_sales FLOAT DEFAULT 0.0,
    delivery_fee FLOAT DEFAULT 0.0,
    ach_fee FLOAT DEFAULT 0.0,
    blazepay_fee FLOAT DEFAULT 0.0,
    aeropay_fee FLOAT DEFAULT 0.0,
    blazepay_ach_fee FLOAT DEFAULT 0.0,
    cashless_atm_fee FLOAT DEFAULT 0.0,
    cash_fee FLOAT DEFAULT 0.0,
    credit_debit_fee FLOAT DEFAULT 0.0,
    stronghold_fee FLOAT DEFAULT 0.0,
    pre_tax_discount FLOAT DEFAULT 0.0,
    adult_net_sales FLOAT DEFAULT 0.0,
    adult_net_sales_wo_fees FLOAT DEFAULT 0.0,
    medical_net_sales FLOAT DEFAULT 0.0,
    medical_net_sales_wo_fees FLOAT DEFAULT 0.0,
    non_cannabis_net_sales FLOAT DEFAULT 0.0,
    non_cannabis_net_sales_wo_fees FLOAT DEFAULT 0.0,
    net_sales FLOAT DEFAULT 0.0,
    net_sales_wo_fees FLOAT DEFAULT 0.0,
    post_al_excise_tax FLOAT DEFAULT 0.0,
    post_nal_excise_tax FLOAT DEFAULT 0.0,
    post_city_tax FLOAT DEFAULT 0.0,
    post_county_tax FLOAT DEFAULT 0.0,
    post_state_tax FLOAT DEFAULT 0.0,
    post_federal_tax FLOAT DEFAULT 0.0,
    delivery_fee_excise_tax FLOAT DEFAULT 0.0,
    city_delivery_fee_tax FLOAT DEFAULT 0.0,
    county_delivery_fee_tax FLOAT DEFAULT 0.0,
    state_delivery_fee_tax FLOAT DEFAULT 0.0,
    federal_delivery_fee_tax FLOAT DEFAULT 0.0,
    adult_total_tax FLOAT DEFAULT 0.0,
    medical_total_tax FLOAT DEFAULT 0.0,
    non_cannabis_total_tax FLOAT DEFAULT 0.0,
    total_tax FLOAT DEFAULT 0.0,
    after_tax_discount FLOAT DEFAULT 0.0,
    rounding FLOAT DEFAULT 0.0,
    adjustments FLOAT DEFAULT 0.0,
    adult_total_due FLOAT DEFAULT 0.0,
    medical_total_due FLOAT DEFAULT 0.0,
    non_cannabis_total_due FLOAT DEFAULT 0.0,
    total_due FLOAT DEFAULT 0.0,
    tips FLOAT DEFAULT 0.0,
    blazepay_tips FLOAT DEFAULT 0.0,
    aeropay_tips FLOAT DEFAULT 0.0,
    blazepay_ach_tips FLOAT DEFAULT 0.0,
    num_transactions INTEGER DEFAULT 0,
    count_completed_sales INTEGER DEFAULT 0,
    count_refunds INTEGER DEFAULT 0,
    new_members INTEGER DEFAULT 0,
    returning_members INTEGER DEFAULT 0,
    adult_cogs FLOAT DEFAULT 0.0,
    medical_cogs FLOAT DEFAULT 0.0,
    non_cannabis_cogs FLOAT DEFAULT 0.0,
    ach_tendered FLOAT DEFAULT 0.0,
    blazepay_tendered FLOAT DEFAULT 0.0,
    aeropay_tendered FLOAT DEFAULT 0.0,
    blazepay_ach_tendered FLOAT DEFAULT 0.0,
    cashless_atm_tendered FLOAT DEFAULT 0.0,
    cash_tendered FLOAT DEFAULT 0.0,
    check_tendered FLOAT DEFAULT 0.0,
    credit_debit_tendered FLOAT DEFAULT 0.0,
    gift_card_tendered FLOAT DEFAULT 0.0,
    birchmount_tendered FLOAT DEFAULT 0.0,
    store_credit_tendered FLOAT DEFAULT 0.0,
    stronghold_tendered FLOAT DEFAULT 0.0,
    payment_tendered FLOAT DEFAULT 0.0,
    ach_change_due FLOAT DEFAULT 0.0,
    blazepay_change_due FLOAT DEFAULT 0.0,
    aeropay_change_due FLOAT DEFAULT 0.0,
    blazepay_ach_change_due FLOAT DEFAULT 0.0,
    cashless_atm_change_due FLOAT DEFAULT 0.0,
    cash_change_due FLOAT DEFAULT 0.0,
    check_change_due FLOAT DEFAULT 0.0,
    credit_debit_change_due FLOAT DEFAULT 0.0,
    gift_card_change_due FLOAT DEFAULT 0.0,
    store_credit_change_due FLOAT DEFAULT 0.0,
    stronghold_change_due FLOAT DEFAULT 0.0,
    change_due FLOAT DEFAULT 0.0,
    items_sold INTEGER DEFAULT 0,
    items_refunded INTEGER DEFAULT 0,
    refund_total_due FLOAT DEFAULT 0.0,
    surcharge_fee_tax FLOAT DEFAULT 0.0,
    blazepay_cashback FLOAT DEFAULT 0.0,
    aeropay_cashback FLOAT DEFAULT 0.0,
    blazepay_ach_cashback FLOAT DEFAULT 0.0,
    cashless_atm_cashback FLOAT DEFAULT 0.0,
    untaxed_fee FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_daily_accounting_summary_line_hash ON daily_accounting_summary(line_hash);
CREATE INDEX IF NOT EXISTS ix_daily_accounting_summary_date ON daily_accounting_summary(date);
CREATE INDEX IF NOT EXISTS ix_daily_accounting_summary_shop ON daily_accounting_summary(shop);
CREATE INDEX IF NOT EXISTS ix_daily_accounting_date_shop ON daily_accounting_summary(date, shop);

-- Cash Drawers table
CREATE TABLE IF NOT EXISTS cash_drawers (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE NOT NULL,
    terminal VARCHAR(100),
    status VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    starting_cash FLOAT DEFAULT 0.0,
    ending_cash FLOAT DEFAULT 0.0,
    paid_in FLOAT DEFAULT 0.0,
    paid_out FLOAT DEFAULT 0.0,
    cash_drops FLOAT DEFAULT 0.0,
    expected_in_drawer FLOAT DEFAULT 0.0,
    actual_in_drawer FLOAT DEFAULT 0.0,
    cash_sales FLOAT DEFAULT 0.0,
    check_sales FLOAT DEFAULT 0.0,
    credit_sales FLOAT DEFAULT 0.0,
    store_credit_sales FLOAT DEFAULT 0.0,
    blazepay_sales FLOAT DEFAULT 0.0,
    ach_sales FLOAT DEFAULT 0.0,
    gift_card_sales FLOAT DEFAULT 0.0,
    cashless_atm_sales FLOAT DEFAULT 0.0,
    cash_received FLOAT DEFAULT 0.0,
    cashless_atm_received FLOAT DEFAULT 0.0,
    cash_change FLOAT DEFAULT 0.0,
    cashless_atm_change FLOAT DEFAULT 0.0,
    cash_refunds FLOAT DEFAULT 0.0,
    check_refunds FLOAT DEFAULT 0.0,
    credit_refunds FLOAT DEFAULT 0.0,
    store_credit_refunds FLOAT DEFAULT 0.0,
    blazepay_refunds FLOAT DEFAULT 0.0,
    ach_refunds FLOAT DEFAULT 0.0,
    gift_card_refunds FLOAT DEFAULT 0.0,
    cashless_atm_refunds FLOAT DEFAULT 0.0,
    blazepay_cashback FLOAT DEFAULT 0.0,
    cash_voids FLOAT DEFAULT 0.0,
    store_credit_voids FLOAT DEFAULT 0.0,
    gift_card_voids FLOAT DEFAULT 0.0,
    blazepay_tips FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_cash_drawers_line_hash ON cash_drawers(line_hash);
CREATE INDEX IF NOT EXISTS ix_cash_drawers_date ON cash_drawers(date);
CREATE INDEX IF NOT EXISTS ix_cash_drawers_terminal ON cash_drawers(terminal);
CREATE INDEX IF NOT EXISTS ix_cash_drawer_date_terminal ON cash_drawers(date, terminal);

-- Integrated Payments table
CREATE TABLE IF NOT EXISTS integrated_payments (
    id VARCHAR(36) PRIMARY KEY,
    third_party_id VARCHAR(100) UNIQUE NOT NULL,
    payment_service_name VARCHAR(100),
    processed_time TIMESTAMP,
    transaction_completion_date DATE,
    transaction_number VARCHAR(50),
    transaction_status VARCHAR(50),
    customer VARCHAR(255),
    total_due FLOAT DEFAULT 0.0,
    paid_amount FLOAT DEFAULT 0.0,
    tip FLOAT DEFAULT 0.0,
    cashback FLOAT DEFAULT 0.0,
    payment_fee FLOAT DEFAULT 0.0,
    gross_payment FLOAT DEFAULT 0.0,
    employee VARCHAR(255),
    terminal_id VARCHAR(100),
    terminal_name VARCHAR(100),
    third_party_terminal_id VARCHAR(100),
    payment_id VARCHAR(100)
);
CREATE INDEX IF NOT EXISTS ix_integrated_payments_third_party_id ON integrated_payments(third_party_id);
CREATE INDEX IF NOT EXISTS ix_integrated_payments_payment_service_name ON integrated_payments(payment_service_name);
CREATE INDEX IF NOT EXISTS ix_integrated_payments_transaction_number ON integrated_payments(transaction_number);
CREATE INDEX IF NOT EXISTS ix_integrated_payments_transaction_completion_date ON integrated_payments(transaction_completion_date);
CREATE INDEX IF NOT EXISTS ix_integrated_payments_date ON integrated_payments(transaction_completion_date);

-- Payments Snapshot table
CREATE TABLE IF NOT EXISTS payments_snapshot (
    id VARCHAR(36) PRIMARY KEY,
    line_hash VARCHAR(64) UNIQUE NOT NULL,
    date DATE NOT NULL,
    shop VARCHAR(255),
    company VARCHAR(500),
    payment_type VARCHAR(50),
    payment_type_usage INTEGER DEFAULT 0,
    queue_type VARCHAR(50),
    total_due FLOAT DEFAULT 0.0,
    cash_back FLOAT DEFAULT 0.0,
    change_due FLOAT DEFAULT 0.0,
    transaction_fee FLOAT DEFAULT 0.0,
    payment_received FLOAT DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS ix_payments_snapshot_line_hash ON payments_snapshot(line_hash);
CREATE INDEX IF NOT EXISTS ix_payments_snapshot_date ON payments_snapshot(date);
CREATE INDEX IF NOT EXISTS ix_payments_snapshot_payment_type ON payments_snapshot(payment_type);
CREATE INDEX IF NOT EXISTS ix_payments_snapshot_date_type ON payments_snapshot(date, payment_type);

-- Log migration completion
SELECT 'Migration 002_create_report_tables completed successfully' AS status;
