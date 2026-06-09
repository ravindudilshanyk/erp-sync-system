"""
Sync Service
------------
Core synchronization logic between ERP system and internal database.

Key concepts:
- Full sync: import everything from ERP regardless of revision
- Delta sync: import only records changed since last successful sync
- Preloading: load all existing records into memory for fast O(1) lookups
- Batch commits: commit every N records instead of one by one
- Skip unchanged: compare before updating to minimize DB operations
- Log and continue: errors on individual records don't stop the whole sync
"""

import logging
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.models import Product, StockItem, Supplier, SyncState
from app.mock_erp.erp_client import (
    fetch_erp_products,
    fetch_erp_pricing_bulk,
    fetch_erp_suppliers,
    get_max_pricing_revision
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# How many records to process before committing to DB
BATCH_SIZE = 100


def get_or_create_sync_state(db: Session) -> SyncState:
    """
    Get existing sync state or create one if it doesn't exist.
    There is always exactly one sync state record.
    """
    state = db.query(SyncState).first()
    if not state:
        state = SyncState()
        db.add(state)
        db.commit()
        db.refresh(state)
        logger.info("Created initial sync state record")
    return state


def sync_suppliers(db: Session, erp_suppliers: list) -> dict:
    """
    Ensure all ERP suppliers exist in our internal database.
    Returns a mapping of erp_id -> internal supplier id for fast lookup.
    """
    logger.info(f"Syncing {len(erp_suppliers)} suppliers from ERP")

    # Preload existing suppliers into memory
    existing_suppliers = {
        s.erp_id: s for s in db.query(Supplier).all()
    }

    for erp_supplier in erp_suppliers:
        if erp_supplier["erp_id"] not in existing_suppliers:
            new_supplier = Supplier(
                erp_id=erp_supplier["erp_id"],
                name=erp_supplier["name"]
            )
            db.add(new_supplier)
            logger.info(f"Created supplier: {erp_supplier['name']}")

    db.commit()

    # Return fresh mapping after any new suppliers were added
    return {
        s.erp_id: s.id
        for s in db.query(Supplier).all()
    }


def run_full_sync(db: Session) -> dict:
    """
    Full synchronization — imports ALL active products from ERP.
    Ignores revision watermarks and processes everything.
    """
    logger.info("=" * 50)
    logger.info("Starting FULL synchronization")
    logger.info("=" * 50)

    return _run_sync(db, full=True)


def run_delta_sync(db: Session) -> dict:
    """
    Delta synchronization — imports only records changed since last sync.
    Uses revision watermarks from SyncState to determine starting point.
    """
    logger.info("=" * 50)
    logger.info("Starting DELTA synchronization")
    logger.info("=" * 50)

    return _run_sync(db, full=False)


def _run_sync(db: Session, full: bool) -> dict:
    """
    Internal sync runner used by both full and delta sync.
    """
    start_time = time.time()

    # ── Step 1: Get current sync state ───────────────────────
    state = get_or_create_sync_state(db)
    state.status = "running"
    db.commit()

    # Determine starting revision
    since_revision = 0 if full else state.last_product_revision
    sync_type = "full" if full else "delta"
    logger.info(f"Sync type: {sync_type} | Since revision: {since_revision}")

    try:
        # ── Step 2: Sync suppliers first ──────────────────────
        erp_suppliers = fetch_erp_suppliers()
        supplier_map = sync_suppliers(db, erp_suppliers)
        logger.info(f"Supplier map loaded: {len(supplier_map)} suppliers")

        # ── Step 3: Fetch products from ERP ──────────────────
        erp_products = fetch_erp_products(since_revision=since_revision)
        logger.info(f"Fetched {len(erp_products)} products from ERP")

        if not erp_products:
            logger.info("No new products to sync — already up to date")

            # Count existing products as skipped for accurate reporting
            total_existing = db.query(Product).count()

            state.status = "success"
            state.total_created = 0
            state.total_updated = 0
            state.total_skipped = total_existing
            state.last_synced_at = datetime.now(timezone.utc)
            db.commit()

            return {
                "message": "Already up to date — all records unchanged",
                "sync_type": sync_type,
                "total_created": 0,
                "total_updated": 0,
                "total_skipped": total_existing,
                "errors": 0,
                "last_product_revision": state.last_product_revision,
                "last_pricing_revision": state.last_pricing_revision,
                "duration_seconds": round(time.time() - start_time, 2)
            }

        # ── Step 4: Fetch pricing in bulk ─────────────────────
        erp_ids = [p["erp_id"] for p in erp_products]
        pricing_data = fetch_erp_pricing_bulk(erp_ids)
        logger.info(f"Fetched pricing for {len(pricing_data)} products")

        # ── Step 5: Preload existing records into memory ──────
        # This is the performance optimization — load once, lookup many times
        # Instead of querying DB for each product (N+1 problem), we use a dict
        existing_products = {
            p.erp_id: p for p in db.query(Product).all()
        }
        existing_stock = {
            s.product_id: s for s in db.query(StockItem).all()
        }
        logger.info(
            f"Preloaded {len(existing_products)} products "
            f"and {len(existing_stock)} stock items into memory"
        )

        # ── Step 6: Process each product ─────────────────────
        created = updated = skipped = error_count = 0

        for i, erp_product in enumerate(erp_products):
            try:
                erp_id = erp_product["erp_id"]
                pricing = pricing_data.get(erp_id)
                supplier_erp_id = erp_product.get("supplier_erp_id")

                # Resolve supplier — log warning if not found but continue
                internal_supplier_id = supplier_map.get(supplier_erp_id)
                if internal_supplier_id is None:
                    logger.warning(
                        f"No supplier mapping for ERP supplier: {supplier_erp_id} "
                        f"(product: {erp_id}) — continuing without supplier"
                    )

                # ── Case 1: Product does not exist → CREATE ───
                if erp_id not in existing_products:
                    new_product = Product(
                        erp_id=erp_id,
                        name=erp_product["name"],
                        sku=erp_product["sku"],
                        revision=erp_product["revision"]
                    )
                    db.add(new_product)
                    db.flush()  # Get product.id without committing

                    new_stock = StockItem(
                        product_id=new_product.id,
                        supplier_id=internal_supplier_id,
                        price=pricing["price"] if pricing else 0.0
                    )
                    db.add(new_stock)
                    created += 1
                    logger.info(f"CREATED: {erp_product['name']} ({erp_id})")

                # ── Case 2: Product exists → check if UPDATE needed ──
                else:
                    product = existing_products[erp_id]
                    stock = existing_stock.get(product.id)

                    # Check what changed
                    current_price = stock.price if stock else None
                    new_price = pricing["price"] if pricing else None
                    price_changed = (current_price != new_price) and new_price is not None
                    supplier_changed = stock and (stock.supplier_id != internal_supplier_id)

                    if price_changed or supplier_changed:
                        if stock:
                            if price_changed:
                                stock.price = new_price
                                logger.info(
                                    f"UPDATED price: {erp_product['name']} "
                                    f"${current_price} → ${new_price}"
                                )
                            if supplier_changed:
                                stock.supplier_id = internal_supplier_id
                                logger.info(
                                    f"UPDATED supplier: {erp_product['name']}"
                                )
                        # Update product revision
                        product.revision = erp_product["revision"]
                        updated += 1
                    else:
                        # Nothing changed — skip to save DB operations
                        skipped += 1
                        logger.debug(f"SKIPPED (unchanged): {erp_id}")

                # ── Batch commit every BATCH_SIZE records ─────
                if (i + 1) % BATCH_SIZE == 0:
                    db.commit()
                    logger.info(
                        f"Batch committed {i + 1}/{len(erp_products)} records "
                        f"(created={created}, updated={updated}, skipped={skipped})"
                    )

            except Exception as e:
                # Log error but continue processing remaining products
                error_count += 1
                logger.error(
                    f"Error processing product {erp_product.get('erp_id', 'unknown')}: "
                    f"{str(e)}"
                )
                continue  # Don't crash — move to next product

        # ── Step 7: Final commit ──────────────────────────────
        db.commit()
        logger.info("Final commit completed")

        # ── Step 8: Calculate revision watermarks ─────────────
        max_product_revision = max(
            p["revision"] for p in erp_products
        ) if erp_products else state.last_product_revision

        max_pricing_revision = get_max_pricing_revision(erp_ids)

        # ── Step 9: Update sync state ─────────────────────────
        state.last_product_revision = max_product_revision
        state.last_pricing_revision = max_pricing_revision
        state.status = "success"
        state.total_created = created
        state.total_updated = updated
        state.total_skipped = skipped
        state.error_message = (
            f"{error_count} errors occurred during sync"
            if error_count > 0 else None
        )
        state.last_synced_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(state)

        duration = round(time.time() - start_time, 2)

        logger.info("=" * 50)
        logger.info(f"Sync completed in {duration}s")
        logger.info(
            f"Created: {created} | Updated: {updated} | "
            f"Skipped: {skipped} | Errors: {error_count}"
        )
        logger.info(
            f"Revision watermarks → Products: {max_product_revision} "
            f"| Pricing: {max_pricing_revision}"
        )
        logger.info("=" * 50)

        return {
            "message": f"{sync_type.capitalize()} sync completed successfully",
            "sync_type": sync_type,
            "total_created": created,
            "total_updated": updated,
            "total_skipped": skipped,
            "errors": error_count,
            "last_product_revision": max_product_revision,
            "last_pricing_revision": max_pricing_revision,
            "duration_seconds": duration
        }

    except Exception as e:
        # Unexpected error — mark sync as failed
        logger.error(f"Sync failed with unexpected error: {str(e)}")
        state.status = "failed"
        state.error_message = str(e)
        db.commit()
        raise