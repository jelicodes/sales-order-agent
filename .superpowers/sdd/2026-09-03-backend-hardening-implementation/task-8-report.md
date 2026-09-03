# Task 8: Add Pydantic input schemas to all tools

**Status:** DONE

## Changes Made

Added explicit `args_schema` (Pydantic `BaseModel`) to all 6 LangChain tools for better tool call validation and clear LLM instructions:

| Tool | Schema Class | Fields |
|------|-------------|--------|
| `search_products` | `SearchProductsInput` | `query`, `category` |
| `get_product_detail` | `GetProductDetailInput` | `product_id` |
| `check_stock` | `CheckStockInput` | `product_id`, `quantity` |
| `calculate_price` | `CalculatePriceInput` | `product_id`, `quantity`, `discount_code` |
| `create_quote` | `CreateQuoteInput` + `QuoteItem` | `items` (nested), `customer_info` |
| `get_alternatives` | `GetAlternativesInput` | `product_id`, `reason` |

## Extra Fix

`create_quote` function body required updating — after adding `args_schema`, items arrive as `QuoteItem` Pydantic objects (not dicts), so dict subscript (`item["product_id"]`) was replaced with attribute access (`item.product_id`). The spread operator `{**item, ...}` was replaced with explicit dict construction.

## Test Results

```
55 passed, 1 warning in 16.31s
```

## Commit

```
ae9c1fd feat: add Pydantic input schemas to all 6 tools
```

## Concerns

None. All tests pass cleanly.
