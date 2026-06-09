from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sync, products

app = FastAPI(
    title="ERP Product Catalog Synchronization",
    description="Synchronizes product master data, supplier mappings, and pricing from an external ERP system into the internal inventory database. Supports full sync and delta sync using revision watermarks.",
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