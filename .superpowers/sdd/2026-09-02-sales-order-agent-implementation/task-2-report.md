# Task 2 Report: Seed Data

## Status: DONE

## Files Created
- `src/data/seed/products.json` — 12 products across 6 categories (Polo, Kaos, Jaket, Seragam, Celana, Aksesoris)
- `src/data/seed/price_tiers.json` — tiered pricing for all 12 products (3-4 tiers each, ~5-10% discount per tier)
- `src/data/seed/stock.json` — stock variants for all 12 products (2-4 colors each, quantities 400-3000, warehouse: Tanah Abang)
- `src/data/seed/discounts.json` — 5 active discount codes (NEWCUSTOMER10, BULK500, HEMAT20K, MERDEKA15, FIRSTORDER)

## Test Summary
All 4 JSON files parse correctly via `json.load()`. Product IDs consistent across files.

## Concerns
None. All data follows specs: IDR currency, Bahasa Indonesia descriptions, correct tier rules per MOQ, valid discount dates.
