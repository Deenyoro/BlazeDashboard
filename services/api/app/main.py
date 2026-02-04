from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional

from app.core.database import engine, Base
from app.api.v1.router import api_router
from app.core.auth import get_current_user, TokenPayload, AUTH_ENABLED
from app.models import (
    Transaction, Member, Employee, Product, ProductSale, InventorySnapshot, DiscountUsage,
    RefundHistory, SalesPayment, SalesByQueue, ReceivedInventory,
    InventoryReconciliation, InventoryAction, DailyAccountingSummary,
    CashDrawer, IntegratedPayment, PaymentsSnapshot,
    Vendor, ProductCatalog, ProductBatch, Consumer,
    EmployeePerformance, EmployeeActivity, TimeClock,
    MemberPerformance, InactiveMember, MarketingContact,
    DeliverySale, CanceledVoidSale, UncompleteSale, PromotionsActivity,
    ProfitLoss, PurchaseOrderByCategory, ReturnToVendor, RefundHistoryDetail,
    PaidInOutActivity, InventoryAging, InventoryDistribution, InventoryValuation,
    InventoryTransfer, SellThrough, CurrentInventory, SalesByCity, SalesByHour,
    SalesByProduct, SalesByProductCategory, SalesByVendor, SalesByConsumerType,
    EmployeeSalesByProduct, ProductsByVendor, ProductSalesByInventory, ProductSellByExpire,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="BlazeDashboard API",
    description="API for viewing and querying exported Blaze POS data",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "blazedashboard-api"}


@app.get("/me")
async def get_me(user: Optional[TokenPayload] = Depends(get_current_user)):
    """Get current authenticated user info"""
    if user is None:
        return {"authenticated": False, "auth_enabled": AUTH_ENABLED}
    return {
        "authenticated": True,
        "sub": user.sub,
        "email": user.email,
        "name": user.name,
        "username": user.preferred_username,
        "roles": user.roles,
    }


@app.get("/")
async def root():
    return {
        "service": "BlazeDashboard API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "transactions": "/api/v1/transactions",
            "stats": "/api/v1/transactions/stats",
            "overview": "/api/v1/transactions/overview",
            "ingest_all": "/api/v1/ingest/all",
            "ingest_all_status": "/api/v1/ingest/all/status",
            "ingest_csv": "/api/v1/ingest/csv",
            "ingest_sales_details": "/api/v1/ingest/sales-details",
            "ingest_refund_history": "/api/v1/ingest/refund-history",
            "ingest_sales_payments": "/api/v1/ingest/sales-payments",
            "ingest_sales_by_queue": "/api/v1/ingest/sales-by-queue",
            "ingest_received_inventory": "/api/v1/ingest/received-inventory",
            "ingest_inventory_snapshot": "/api/v1/ingest/inventory-snapshot",
            "ingest_inventory_reconciliation": "/api/v1/ingest/inventory-reconciliation",
            "ingest_inventory_actions": "/api/v1/ingest/inventory-actions",
            "ingest_daily_accounting": "/api/v1/ingest/daily-accounting",
            "ingest_cash_drawer": "/api/v1/ingest/cash-drawer",
            "ingest_discount_usage": "/api/v1/ingest/discount-usage",
            "ingest_integrated_payments": "/api/v1/ingest/integrated-payments",
            "ingest_payments_snapshot": "/api/v1/ingest/payments-snapshot",
            "status": "/api/v1/ingest/status",
        },
    }
