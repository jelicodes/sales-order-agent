# Task 12: Fix discount min_qty validation — Report

## What I Implemented

Added `min_qty` validation to `calculate_price` tool so discounts are only applied when the order quantity meets the discount's minimum requirement.

**Change in `src/tools/calculate_price.py`**: Before applying a discount, check `discount.get("min_qty")`. If the quantity is below the minimum, the discount is skipped (set to `None`).

## Tests Updated

- `tests/test_tools.py` — `test_discount_min_qty_not_met`: Now asserts `discount` is `None` and `discount_amount` is 0 (previously asserted `discount is not None`).
- `tests/test_tools_extended.py` — `test_discount_min_qty_validates_correctly` (renamed from `test_discount_min_qty_not_enforced`): Same updated assertions.

## Test Results

58/58 passing, output pristine (1 unrelated StarletteDeprecationWarning).

## Files Changed

- `src/tools/calculate_price.py`
- `tests/test_tools.py`
- `tests/test_tools_extended.py`

## Self-Review

No concerns. The implementation is minimal and follows the exact pattern specified in the task brief. Existing discount tests (percentage discount with BULK500 at qty 500, fixed discount with HEMAT20K at qty 200) continue to pass, confirming the fix only blocks discounts when min_qty is not met.
