from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sync, products

app = FastAPI(
    title="ERP Product Catalog Synchronization",
    description="""
    ## ERP Product Catalog Synchronization Service

    Synchronizes product master data, supplier mappings, and pricing information
    from an external ERP system into the internal inventory platform.

    ### Key Features
    - **Full Sync** — imports all active products from ERP
    - **Delta Sync** — imports only records changed since last sync
    - **Supplier Resolution** — maps ERP supplier IDs to internal suppliers
    - **Performance Optimized** — bulk retrieval, in-memory lookups, batch commits
    - **Sync State Tracking** — maintains revision watermarks for delta sync

    ### How to Test
    1. `POST /api/sync/full` — run full sync to import all products
    2. `GET /api/sync/status` — check sync state and revision watermarks
    3. `GET /api/products` — view synced products with pricing and supplier info
    4. `POST /api/sync/delta` — run delta sync (will skip unchanged records)
    5. `GET /api/sync/status` — see updated watermarks
    """,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    sync.router,
    prefix="/api/sync",
    tags=["Synchronization"]
)

app.include_router(
    products.router,
    prefix="/api/products",
    tags=["Products"]
)


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "ERP Sync Service is running",
        "status": "healthy",
        "docs": "/docs"
    }