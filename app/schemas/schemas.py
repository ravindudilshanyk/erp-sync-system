from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ─── Supplier Schemas ─────────────────────────────────────────

class SupplierResponse(BaseModel):
    id: int
    name: str
    erp_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Stock Item Schemas ───────────────────────────────────────

class StockItemResponse(BaseModel):
    id: int
    price: float
    supplier: Optional[SupplierResponse] = None

    class Config:
        from_attributes = True


# ─── Product Schemas ──────────────────────────────────────────

class ProductResponse(BaseModel):
    id: int
    erp_id: str
    name: str
    sku: str
    revision: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    stock_item: Optional[StockItemResponse] = None

    class Config:
        from_attributes = True


# ─── Sync Schemas ─────────────────────────────────────────────

class SyncResult(BaseModel):
    message: str
    sync_type: str
    total_created: int
    total_updated: int
    total_skipped: int
    errors: int
    last_product_revision: int
    last_pricing_revision: int
    duration_seconds: float


class SyncStateResponse(BaseModel):
    id: int
    last_product_revision: int
    last_pricing_revision: int
    status: str
    total_created: int
    total_updated: int
    total_skipped: int
    error_message: Optional[str] = None
    last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True