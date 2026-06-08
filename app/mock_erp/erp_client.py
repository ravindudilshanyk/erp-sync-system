"""
Mock ERP Client
--------------
Simulates the external ERP system API.
In a real project this would make HTTP calls to the ERP system.
For this assessment we return realistic mock data.
"""

from typing import List, Dict, Optional


# ─── Mock ERP Data ────────────────────────────────────────────

# Simulated ERP product master records
MOCK_ERP_PRODUCTS = [
    {
        "erp_id": "ERP-PROD-001",
        "name": "Wireless Bluetooth Headphones",
        "sku": "WBH-001",
        "supplier_erp_id": "ERP-SUP-001",
        "revision": 1
    },
    {
        "erp_id": "ERP-PROD-002",
        "name": "USB-C Charging Cable 2m",
        "sku": "UCC-002",
        "supplier_erp_id": "ERP-SUP-001",
        "revision": 2
    },
    {
        "erp_id": "ERP-PROD-003",
        "name": "Mechanical Keyboard RGB",
        "sku": "MKR-003",
        "supplier_erp_id": "ERP-SUP-002",
        "revision": 3
    },
    {
        "erp_id": "ERP-PROD-004",
        "name": "27 inch 4K Monitor",
        "sku": "MON-004",
        "supplier_erp_id": "ERP-SUP-002",
        "revision": 4
    },
    {
        "erp_id": "ERP-PROD-005",
        "name": "Ergonomic Mouse",
        "sku": "EMO-005",
        "supplier_erp_id": "ERP-SUP-003",
        "revision": 5
    },
    {
        "erp_id": "ERP-PROD-006",
        "name": "Laptop Stand Adjustable",
        "sku": "LSA-006",
        "supplier_erp_id": "ERP-SUP-003",
        "revision": 6
    },
    {
        "erp_id": "ERP-PROD-007",
        "name": "Webcam HD 1080p",
        "sku": "WCM-007",
        "supplier_erp_id": "ERP-SUP-004",
        "revision": 7
    },
    {
        "erp_id": "ERP-PROD-008",
        "name": "USB Hub 7 Port",
        "sku": "UHB-008",
        "supplier_erp_id": "ERP-SUP-004",
        "revision": 8
    },
]

# Simulated ERP supplier pricing records
MOCK_ERP_PRICING = {
    "ERP-PROD-001": {"price": 89.99,  "pricing_revision": 1},
    "ERP-PROD-002": {"price": 12.99,  "pricing_revision": 2},
    "ERP-PROD-003": {"price": 149.99, "pricing_revision": 3},
    "ERP-PROD-004": {"price": 599.99, "pricing_revision": 4},
    "ERP-PROD-005": {"price": 45.99,  "pricing_revision": 5},
    "ERP-PROD-006": {"price": 35.99,  "pricing_revision": 6},
    "ERP-PROD-007": {"price": 79.99,  "pricing_revision": 7},
    "ERP-PROD-008": {"price": 29.99,  "pricing_revision": 8},
}

# Simulated ERP supplier master records
MOCK_ERP_SUPPLIERS = [
    {"erp_id": "ERP-SUP-001", "name": "TechSupply Co"},
    {"erp_id": "ERP-SUP-002", "name": "GlobalTech Distributors"},
    {"erp_id": "ERP-SUP-003", "name": "OfficeGear Ltd"},
    {"erp_id": "ERP-SUP-004", "name": "DigitalParts Inc"},
]


# ─── ERP Client Functions ─────────────────────────────────────

def fetch_erp_products(since_revision: int = 0) -> List[Dict]:
    """
    Fetch product master records from ERP.
    since_revision=0 means full sync (all products).
    since_revision>0 means delta sync (only changed products).
    """
    return [
        product for product in MOCK_ERP_PRODUCTS
        if product["revision"] > since_revision
    ]


def fetch_erp_pricing_bulk(erp_product_ids: List[str]) -> Dict[str, Dict]:
    """
    Fetch supplier pricing for multiple products at once.
    Returns a dict keyed by erp_product_id for fast lookup.
    Bulk retrieval is a performance optimization — one call instead of N calls.
    """
    return {
        erp_id: MOCK_ERP_PRICING[erp_id]
        for erp_id in erp_product_ids
        if erp_id in MOCK_ERP_PRICING
    }


def fetch_erp_suppliers() -> List[Dict]:
    """
    Fetch all supplier records from ERP.
    Used during full sync to ensure all suppliers exist internally.
    """
    return MOCK_ERP_SUPPLIERS


def get_max_pricing_revision(erp_product_ids: List[str]) -> int:
    """
    Get the highest pricing revision from the fetched products.
    Used to update the sync state watermark.
    """
    if not erp_product_ids:
        return 0
    revisions = [
        MOCK_ERP_PRICING[eid]["pricing_revision"]
        for eid in erp_product_ids
        if eid in MOCK_ERP_PRICING
    ]
    return max(revisions) if revisions else 0


# import httpx
# import os
# from dotenv import load_dotenv

# load_dotenv()

# ERP_BASE_URL = os.getenv("ERP_BASE_URL")
# ERP_API_KEY  = os.getenv("ERP_API_KEY")

# HEADERS = {
#     "Authorization": f"Bearer {ERP_API_KEY}",
#     "Content-Type": "application/json"
# }


# def fetch_erp_products(since_revision: int = 0):
#     response = httpx.get(
#         f"{ERP_BASE_URL}/products",
#         headers=HEADERS,
#         params={"since_revision": since_revision}
#     )
#     response.raise_for_status()
#     return response.json()


# def fetch_erp_pricing_bulk(erp_product_ids: list):
#     response = httpx.post(
#         f"{ERP_BASE_URL}/pricing/bulk",
#         headers=HEADERS,
#         json={"product_ids": erp_product_ids}
#     )
#     response.raise_for_status()
#     return response.json()


# def fetch_erp_suppliers():
#     response = httpx.get(
#         f"{ERP_BASE_URL}/suppliers",
#         headers=HEADERS
#     )
#     response.raise_for_status()
#     return response.json()


# def get_max_pricing_revision(erp_product_ids: list):
#     pricing = fetch_erp_pricing_bulk(erp_product_ids)
#     revisions = [p["pricing_revision"] for p in pricing.values() if "pricing_revision" in p]
#     return max(revisions) if revisions else 0