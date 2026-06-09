from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.models.models import Product, StockItem, Supplier
from app.schemas.schemas import ProductResponse

router = APIRouter()


@router.get(
    "/",
    response_model=List[ProductResponse],
    summary="List All Products",
    description="Returns all synced products with their stock items and supplier info."
)
def get_products(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = Query(None, description="Search by product name or SKU"),
    db: Session = Depends(get_db)
):
    query = db.query(Product).options(
        joinedload(Product.stock_item).joinedload(StockItem.supplier)
    )

    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%") |
            Product.sku.ilike(f"%{search}%")
        )

    return query.offset(skip).limit(limit).all()


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get Single Product",
    description="Returns a single product with full stock item and supplier details."
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).options(
        joinedload(Product.stock_item).joinedload(StockItem.supplier)
    ).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )

    return product


@router.get(
    "/erp/{erp_id}",
    response_model=ProductResponse,
    summary="Get Product by ERP ID",
    description="Find a product using its ERP system identifier."
)
def get_product_by_erp_id(erp_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).options(
        joinedload(Product.stock_item).joinedload(StockItem.supplier)
    ).filter(Product.erp_id == erp_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ERP ID {erp_id} not found"
        )

    return product