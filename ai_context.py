"""
AI context for the Discounts module.
Loaded into the assistant system prompt when this module's tools are active.
"""

CONTEXT = """
## Module Knowledge: Discounts

### Models

**Coupon** — Code-based discounts customers enter manually.
- `code` (CharField, indexed): The coupon code customers enter
- `name`, `description`: Internal label
- `discount_type`: 'percentage' | 'fixed' | 'buy_x_get_y'
- `discount_value`: Amount or percent value (must be > 0)
- `scope`: 'order' | 'products' | 'categories' — what it applies to
- `min_purchase`: Minimum order total required (default 0.00)
- `max_discount`: Cap on discount amount (optional)
- `usage_limit`: Total uses allowed (null = unlimited)
- `usage_per_customer`: Uses per customer (default 1)
- `usage_count`: Running total of uses
- `valid_from` / `valid_until`: Validity window
- `buy_quantity` / `get_quantity` / `get_discount_percent`: For buy_x_get_y type
- `priority`: Higher = applied first when stacking
- `stackable`: Can be combined with other discounts
- `is_active`: Boolean toggle
- Status (computed): 'active' | 'inactive' | 'exhausted' | 'scheduled' | 'expired'

**Promotion** — Auto-applied, time-based discounts (no code needed).
- Same discount_type, discount_value, scope, min_purchase, max_discount as Coupon
- `valid_from` / `valid_until`: Required date range
- `days_of_week`: Comma-separated integers (0=Mon, 6=Sun); empty = all days
- `start_time` / `end_time`: Time-of-day window (optional)
- `priority` (0-100), `stackable`
- `is_active`
- Status: 'active' | 'inactive' | 'scheduled' | 'expired'

**CouponProduct** / **CouponCategory**: Scope targeting for coupons with scope='products'/'categories'.
**PromotionProduct** / **PromotionCategory**: Same for promotions.

**DiscountCondition** — Extra conditions on a coupon or promotion.
- `coupon` or `promotion` FK (one must be set)
- `condition_type`: 'min_quantity' | 'min_amount' | 'customer_group' | 'first_purchase' | 'day_of_week' | 'time_of_day'
- `value`: JSON or plain text depending on type
- `is_inclusive`: True = must match; False = must NOT match

**DiscountUsage** — Usage tracking record.
- `coupon` or `promotion` FK
- `sale` FK → sales.Sale
- `customer` FK → customers.Customer
- `amount_discounted`, `original_amount`
- `used_at`

### Key Flows

1. **Apply coupon**: Check `Coupon.can_use(customer, order_total)` → `calculate_discount(order_total)` → increment `usage_count` → create `DiscountUsage`
2. **Auto-apply promotion**: Check `Promotion.is_valid` (status + days_of_week + time window) → `calculate_discount(order_total)` → create `DiscountUsage`
3. **buy_x_get_y**: Set `buy_quantity`, `get_quantity`, `get_discount_percent`; `discount_type` must be 'buy_x_get_y' (calculate_discount returns 0 — logic is in sale processing)
4. **Scope filtering**: If scope='products', add products via CouponProduct/PromotionProduct; if 'categories', via CouponCategory/PromotionCategory

### Relationships
- `DiscountUsage.sale` → sales.Sale
- `DiscountUsage.customer` → customers.Customer
- `CouponProduct.product` / `PromotionProduct.product` → inventory.Product
- `CouponCategory.category` / `PromotionCategory.category` → inventory.Category
"""
