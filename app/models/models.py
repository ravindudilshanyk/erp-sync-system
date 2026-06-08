from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Supplier(Base):
    """
    Internal supplier record.
    erp_id links to the ERP system's supplier identifier.
    """
    __tablename__ = "suppliers"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    erp_id     = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    stock_items = relationship("StockItem", back_populates="supplier")


class Product(Base):
    """
    Internal product record.
    erp_id links to the ERP system's product identifier.
    revision tracks what version we last synced from ERP.
    """
    __tablename__ = "products"

    id         = Column(Integer, primary_key=True, index=True)
    erp_id     = Column(String(50), unique=True, nullable=False, index=True)
    name       = Column(String(200), nullable=False)
    sku        = Column(String(100), unique=True, nullable=False)
    revision   = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    stock_item = relationship("StockItem", back_populates="product", uselist=False)


class StockItem(Base):
    """
    Inventory record linked to a product.
    Holds current price and supplier mapping.
    Updated when ERP pricing or supplier data changes.
    """
    __tablename__ = "stock_items"

    id          = Column(Integer, primary_key=True, index=True)
    price       = Column(Float, default=0.0)
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    product_id  = Column(Integer, ForeignKey("products.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    product     = relationship("Product", back_populates="stock_item")
    supplier    = relationship("Supplier", back_populates="stock_items")


class SyncState(Base):
    """
    Tracks the synchronization state between ERP and internal system.
    Maintains revision watermarks so delta sync knows where to start.
    """
    __tablename__ = "sync_state"

    id                    = Column(Integer, primary_key=True, index=True)
    last_product_revision = Column(Integer, default=0)
    last_pricing_revision = Column(Integer, default=0)
    status                = Column(String(50), default="idle")
    total_created         = Column(Integer, default=0)
    total_updated         = Column(Integer, default=0)
    total_skipped         = Column(Integer, default=0)
    error_message         = Column(String(500), nullable=True)
    last_synced_at        = Column(DateTime(timezone=True), nullable=True)