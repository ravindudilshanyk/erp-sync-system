# ERP Product Catalog Synchronization

A production-ready ERP synchronization service built with **FastAPI** and **PostgreSQL**.

## Overview

Synchronizes product master data, supplier mappings, and pricing information 
from an external ERP system into an internal inventory database.

Supports two sync modes:
- **Full Sync** — imports all active products regardless of revision
- **Delta Sync** — imports only records changed since last sync using revision watermarks

## Tech Stack

- **FastAPI** — REST API framework
- **PostgreSQL** — internal database
- **SQLAlchemy** — ORM
- **Alembic** — database migrations

## Project Structure