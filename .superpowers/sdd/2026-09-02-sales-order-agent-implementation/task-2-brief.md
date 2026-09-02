# Task 2: Seed Data (Products, Pricing, Stock, Discounts)

## Files to Create
- `src/data/seed/products.json`
- `src/data/seed/price_tiers.json`
- `src/data/seed/stock.json`
- `src/data/seed/discounts.json`

## What to Do

Create 4 JSON files with synthetic data for PT Lemone fashion wholesale B2B.

### products.json — 12 products across 6 categories

Create `src/data/seed/` directory, then create `products.json` with these 12 products:

| ID | Name | Category | Base Price | MOQ | Lead Time |
|----|------|----------|------------|-----|-----------|
| 1 | Polo Premium Cotton | Polo | 85000 | 100 | 5 |
| 2 | Polo Basic | Polo | 65000 | 100 | 5 |
| 3 | Kaos Polos Premium | Kaos | 55000 | 50 | 3 |
| 4 | Kaos Polos Standar | Kaos | 35000 | 50 | 3 |
| 5 | Jaket Bomber Kulit | Jaket | 250000 | 25 | 7 |
| 6 | Jaket Hoodie Premium | Jaket | 180000 | 50 | 7 |
| 7 | Seragam Kantor Putih | Seragam | 120000 | 30 | 5 |
| 8 | Seragam Kerja Navy | Seragam | 95000 | 30 | 5 |
| 9 | Celana Chino Premium | Celana | 145000 | 30 | 7 |
| 10 | Celana Jogger Kantor | Celana | 130000 | 30 | 7 |
| 11 | Tas Selempang Premium | Aksesoris | 85000 | 50 | 5 |
| 12 | Topi Baseball Custom | Aksesoris | 45000 | 100 | 5 |

Each product should have: id, name, category, description (2 sentences in Bahasa Indonesia), base_price, moq, lead_time_days.

### price_tiers.json — tiered pricing per product

Create price tiers with these rules:
- Products with MOQ 50: tiers 1-99, 100-299, 300-499, 500+
- Products with MOQ 100: tiers 1-99, 100-299, 300-499, 500+
- Products with MOQ 25-30: tiers 1-29/49, 30-99, 100+

Price per unit decreases ~5-10% per tier. Use the exact prices from the plan's JSON.

### stock.json — stock per variant

Create stock entries for each product with 2-4 color variants. Quantities between 200-3000. All warehouse: "Tanah Abang".

### discounts.json — 5 active discounts

| Code | Type | Value | Min Qty | Valid Until |
|------|------|-------|---------|-------------|
| NEWCUSTOMER10 | percentage | 10 | 100 | 2026-12-31 |
| BULK500 | percentage | 5 | 500 | 2026-12-31 |
| HEMAT20K | fixed | 20000 | 200 | 2026-10-31 |
| MERDEKA15 | percentage | 15 | 100 | 2026-08-31 |
| FIRSTORDER | percentage | 8 | 50 | 2026-12-31 |

## Verification
- All JSON files parse correctly: `python -c "import json; json.load(open('src/data/seed/products.json'))"`
- Product IDs are consistent across files

## Report
Write your report to: `.superpowers/sdd/2026-09-02-sales-order-agent-implementation/task-2-report.md`
