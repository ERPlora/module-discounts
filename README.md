# Discounts Module

Promotions, coupons, and discount management for POS.

## Features

- **Coupons**: Code-based discounts with percentage, fixed amount, or Buy X Get Y types
- **Promotions**: Auto-applied, time-based discounts with scheduling (days of week, time windows)
- Scope targeting: apply discounts to entire orders, specific products, or specific categories
- Minimum purchase requirements and maximum discount caps
- Usage limits (total and per customer) with tracking
- Validity periods with scheduled activation
- Discount stacking control with priority ordering
- Flexible conditions: minimum quantity, minimum amount, customer group, first purchase, day of week, time of day
- Full usage tracking with amount discounted and original amount recorded
- Coupon validation logic (status checks, customer limits, purchase minimums)
- Dashboard overview of active promotions and coupon performance

## Installation

This module is installed automatically via the ERPlora Marketplace.

**Dependencies**: Requires `inventory`, `sales`, and `customers` modules.

## Configuration

Access settings via: **Menu > Discounts > Settings**

Default settings include:
- Enable/disable coupons
- Enable/disable promotions
- Maximum discount percentage
- Allow/disallow discount stacking

## Usage

Access via: **Menu > Discounts**

### Views

| View | URL | Description |
|------|-----|-------------|
| Overview | `/m/discounts/dashboard/` | Dashboard with active discount metrics |
| Promotions | `/m/discounts/promotions/` | Create and manage auto-applied promotions |
| Coupons | `/m/discounts/coupons/` | Create and manage coupon codes |
| Settings | `/m/discounts/settings/` | Module configuration |

## Models

| Model | Description |
|-------|-------------|
| `Coupon` | Code-based discount with type (percentage/fixed/buy-x-get-y), scope, usage limits, validity period, and stacking options |
| `Promotion` | Auto-applied discount with scheduling (days of week, time windows), validity period, and priority |
| `CouponProduct` | Links a coupon to specific products for product-scoped discounts |
| `CouponCategory` | Links a coupon to specific categories for category-scoped discounts |
| `PromotionProduct` | Links a promotion to specific products for product-scoped discounts |
| `PromotionCategory` | Links a promotion to specific categories for category-scoped discounts |
| `DiscountCondition` | Flexible condition attached to a coupon or promotion (min quantity, min amount, customer group, etc.) |
| `DiscountUsage` | Tracks each use of a coupon or promotion, recording the sale, customer, and amounts |

## Permissions

| Permission | Description |
|------------|-------------|
| `discounts.view_discount` | View discount rules |
| `discounts.add_discount` | Create new discount rules |
| `discounts.change_discount` | Edit existing discount rules |
| `discounts.delete_discount` | Delete discount rules |
| `discounts.view_coupon` | View coupons |
| `discounts.add_coupon` | Create new coupons |
| `discounts.change_coupon` | Edit existing coupons |
| `discounts.delete_coupon` | Delete coupons |
| `discounts.view_promotion` | View promotions |
| `discounts.add_promotion` | Create new promotions |
| `discounts.change_promotion` | Edit existing promotions |
| `discounts.delete_promotion` | Delete promotions |

## Integration with Other Modules

- **inventory**: Product and category scoping for coupons and promotions via `inventory.Product` and `inventory.Category`
- **sales**: Usage tracking links to `sales.Sale` to record which sale used a discount
- **customers**: Per-customer usage limits and tracking via `customers.Customer`

## License

MIT

## Author

ERPlora Team - support@erplora.com
