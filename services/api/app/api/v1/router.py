from fastapi import APIRouter

from app.api.v1.endpoints import transactions, ingestion, employees, reports, customers, products_catalog

api_router = APIRouter()

api_router.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["transactions"],
)

api_router.include_router(
    ingestion.router,
    prefix="/ingest",
    tags=["ingestion"],
)

api_router.include_router(
    employees.router,
    prefix="/employees",
    tags=["employees"],
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["reports"],
)

api_router.include_router(
    customers.router,
    prefix="/customers",
    tags=["customers"],
)

api_router.include_router(
    products_catalog.router,
    prefix="/products",
    tags=["products"],
)
