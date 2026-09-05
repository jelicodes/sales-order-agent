# ADR-0004: SQLite for Structured Data

## Status

Accepted

## Context

The system needs structured storage for products, prices, stock, orders, and customers. Requirements:
- ACID transactions for order management
- No external server dependency (simplicity)
- Sufficient for single-tenant deployment
- Easy backup and migration

Options considered:
1. **PostgreSQL** — powerful but requires separate server
2. **SQLite** — zero-config, file-based, sufficient for our scale
3. **MongoDB** — flexible schema but unnecessary for structured data

## Decision

Use **SQLite** for all structured data. Three tables: `products`, `prices` (tier-based), `stock` (per-variant). Additional tables for orders and customers. Indexed for fast lookups.

## Consequences

- Zero infrastructure — just a file at `data/app.db`
- TTL caching via `cachetools` for frequently-read static data
- `asyncio.to_thread()` wrapping for non-blocking async access
- Backup = copy the `.db` file
