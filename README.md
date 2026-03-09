# Discounts

## Overview

| Property | Value |
|----------|-------|
| **Module ID** | `discounts` |
| **Version** | `1.0.0` |
| **Icon** | `pricetag-outline` |
| **Dependencies** | `inventory`, `sales`, `customers` |

## Dependencies

This module requires the following modules to be installed:

- `inventory`
- `sales`
- `customers`

## Models

### `Coupon`

Coupon(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, code, name, description, discount_type, discount_value, scope, min_purchase, max_discount, usage_limit, usage_per_customer, usage_count, valid_from, valid_until, buy_quantity, get_quantity, get_discount_percent, priority, stackable, is_active)

| Field | Type | Details |
|-------|------|---------|
| `code` | CharField | max_length=50 |
| `name` | CharField | max_length=100 |
| `description` | TextField | optional |
| `discount_type` | CharField | max_length=20, choices: percentage, fixed, buy_x_get_y |
| `discount_value` | DecimalField |  |
| `scope` | CharField | max_length=20, choices: order, products, categories |
| `min_purchase` | DecimalField |  |
| `max_discount` | DecimalField | optional |
| `usage_limit` | PositiveIntegerField | optional |
| `usage_per_customer` | PositiveIntegerField |  |
| `usage_count` | PositiveIntegerField |  |
| `valid_from` | DateTimeField |  |
| `valid_until` | DateTimeField | optional |
| `buy_quantity` | PositiveIntegerField | optional |
| `get_quantity` | PositiveIntegerField | optional |
| `get_discount_percent` | DecimalField | optional |
| `priority` | PositiveIntegerField |  |
| `stackable` | BooleanField |  |
| `is_active` | BooleanField |  |

**Methods:**

- `can_use()`
- `calculate_discount()`
- `increment_usage()`

**Properties:**

- `status`
- `is_valid`
- `remaining_uses`

### `Promotion`

Promotion(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, name, description, discount_type, discount_value, scope, min_purchase, max_discount, valid_from, valid_until, days_of_week, start_time, end_time, buy_quantity, get_quantity, get_discount_percent, priority, stackable, is_active)

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=100 |
| `description` | TextField | optional |
| `discount_type` | CharField | max_length=20, choices: percentage, fixed, buy_x_get_y |
| `discount_value` | DecimalField |  |
| `scope` | CharField | max_length=20, choices: order, products, categories |
| `min_purchase` | DecimalField | optional |
| `max_discount` | DecimalField | optional |
| `valid_from` | DateTimeField |  |
| `valid_until` | DateTimeField |  |
| `days_of_week` | CharField | max_length=20, optional |
| `start_time` | TimeField | optional |
| `end_time` | TimeField | optional |
| `buy_quantity` | PositiveIntegerField | optional |
| `get_quantity` | PositiveIntegerField | optional |
| `get_discount_percent` | DecimalField | optional |
| `priority` | PositiveIntegerField |  |
| `stackable` | BooleanField |  |
| `is_active` | BooleanField |  |

**Methods:**

- `calculate_discount()`

**Properties:**

- `status`
- `is_valid`

### `CouponProduct`

CouponProduct(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, coupon, product)

| Field | Type | Details |
|-------|------|---------|
| `coupon` | ForeignKey | → `discounts.Coupon`, on_delete=CASCADE |
| `product` | ForeignKey | → `inventory.Product`, on_delete=CASCADE |

### `CouponCategory`

CouponCategory(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, coupon, category)

| Field | Type | Details |
|-------|------|---------|
| `coupon` | ForeignKey | → `discounts.Coupon`, on_delete=CASCADE |
| `category` | ForeignKey | → `inventory.Category`, on_delete=CASCADE |

### `PromotionProduct`

PromotionProduct(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, promotion, product)

| Field | Type | Details |
|-------|------|---------|
| `promotion` | ForeignKey | → `discounts.Promotion`, on_delete=CASCADE |
| `product` | ForeignKey | → `inventory.Product`, on_delete=CASCADE |

### `PromotionCategory`

PromotionCategory(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, promotion, category)

| Field | Type | Details |
|-------|------|---------|
| `promotion` | ForeignKey | → `discounts.Promotion`, on_delete=CASCADE |
| `category` | ForeignKey | → `inventory.Category`, on_delete=CASCADE |

### `DiscountCondition`

DiscountCondition(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, coupon, promotion, condition_type, value, is_inclusive)

| Field | Type | Details |
|-------|------|---------|
| `coupon` | ForeignKey | → `discounts.Coupon`, on_delete=CASCADE, optional |
| `promotion` | ForeignKey | → `discounts.Promotion`, on_delete=CASCADE, optional |
| `condition_type` | CharField | max_length=30, choices: min_quantity, min_amount, customer_group, first_purchase, day_of_week, time_of_day |
| `value` | TextField |  |
| `is_inclusive` | BooleanField |  |

### `DiscountUsage`

DiscountUsage(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, coupon, promotion, sale, customer, amount_discounted, original_amount, used_at, notes)

| Field | Type | Details |
|-------|------|---------|
| `coupon` | ForeignKey | → `discounts.Coupon`, on_delete=CASCADE, optional |
| `promotion` | ForeignKey | → `discounts.Promotion`, on_delete=CASCADE, optional |
| `sale` | ForeignKey | → `sales.Sale`, on_delete=SET_NULL, optional |
| `customer` | ForeignKey | → `customers.Customer`, on_delete=SET_NULL, optional |
| `amount_discounted` | DecimalField |  |
| `original_amount` | DecimalField |  |
| `used_at` | DateTimeField |  |
| `notes` | TextField | optional |

**Properties:**

- `savings_percentage`

## Cross-Module Relationships

| From | Field | To | on_delete | Nullable |
|------|-------|----|-----------|----------|
| `CouponProduct` | `coupon` | `discounts.Coupon` | CASCADE | No |
| `CouponProduct` | `product` | `inventory.Product` | CASCADE | No |
| `CouponCategory` | `coupon` | `discounts.Coupon` | CASCADE | No |
| `CouponCategory` | `category` | `inventory.Category` | CASCADE | No |
| `PromotionProduct` | `promotion` | `discounts.Promotion` | CASCADE | No |
| `PromotionProduct` | `product` | `inventory.Product` | CASCADE | No |
| `PromotionCategory` | `promotion` | `discounts.Promotion` | CASCADE | No |
| `PromotionCategory` | `category` | `inventory.Category` | CASCADE | No |
| `DiscountCondition` | `coupon` | `discounts.Coupon` | CASCADE | Yes |
| `DiscountCondition` | `promotion` | `discounts.Promotion` | CASCADE | Yes |
| `DiscountUsage` | `coupon` | `discounts.Coupon` | CASCADE | Yes |
| `DiscountUsage` | `promotion` | `discounts.Promotion` | CASCADE | Yes |
| `DiscountUsage` | `sale` | `sales.Sale` | SET_NULL | Yes |
| `DiscountUsage` | `customer` | `customers.Customer` | SET_NULL | Yes |

## URL Endpoints

Base path: `/m/discounts/`

| Path | Name | Method |
|------|------|--------|
| `(root)` | `discounts:usage_report` | GET |
| `coupons/` | `coupon_list` | GET |
| `coupons/new/` | `coupon_create` | GET/POST |
| `coupons/<uuid:coupon_id>/` | `coupon_detail` | GET |
| `coupons/<uuid:coupon_id>/edit/` | `coupon_edit` | GET |
| `coupons/<uuid:coupon_id>/delete/` | `coupon_delete` | GET/POST |
| `coupons/<uuid:coupon_id>/toggle/` | `coupon_toggle` | GET |
| `coupons/<uuid:coupon_id>/conditions/add/` | `coupon_condition_add` | GET/POST |
| `promotions/` | `promotion_list` | GET |
| `promotions/new/` | `promotion_create` | GET/POST |
| `promotions/<uuid:promotion_id>/` | `promotion_detail` | GET |
| `promotions/<uuid:promotion_id>/edit/` | `promotion_edit` | GET |
| `promotions/<uuid:promotion_id>/delete/` | `promotion_delete` | GET/POST |
| `promotions/<uuid:promotion_id>/toggle/` | `promotion_toggle` | GET |
| `promotions/<uuid:promotion_id>/conditions/add/` | `promotion_condition_add` | GET/POST |
| `conditions/<uuid:condition_id>/delete/` | `condition_delete` | GET/POST |
| `usage/` | `usage_report` | GET |
| `settings/` | `settings` | GET |
| `api/validate-coupon/` | `api_validate_coupon` | GET |
| `api/active-promotions/` | `api_active_promotions` | GET |
| `api/calculate-discounts/` | `api_calculate_discounts` | GET |
| `api/apply-discount/` | `api_apply_discount` | GET |

## Permissions

| Permission | Description |
|------------|-------------|
| `discounts.view_discount` | View Discount |
| `discounts.add_discount` | Add Discount |
| `discounts.change_discount` | Change Discount |
| `discounts.delete_discount` | Delete Discount |
| `discounts.view_coupon` | View Coupon |
| `discounts.add_coupon` | Add Coupon |
| `discounts.change_coupon` | Change Coupon |
| `discounts.delete_coupon` | Delete Coupon |
| `discounts.view_promotion` | View Promotion |
| `discounts.add_promotion` | Add Promotion |
| `discounts.change_promotion` | Change Promotion |
| `discounts.delete_promotion` | Delete Promotion |
| `discounts.manage_settings` | Manage Settings |

**Role assignments:**

- **admin**: All permissions
- **manager**: `add_coupon`, `add_discount`, `add_promotion`, `change_coupon`, `change_discount`, `change_promotion`, `view_coupon`, `view_discount` (+1 more)
- **employee**: `add_discount`, `view_coupon`, `view_discount`, `view_promotion`

## Navigation

| View | Icon | ID | Fullpage |
|------|------|----|----------|
| Overview | `grid-outline` | `dashboard` | No |
| Promotions | `megaphone-outline` | `promotions` | No |
| Coupons | `ticket-outline` | `coupons` | No |
| Settings | `settings-outline` | `settings` | No |

## AI Tools

Tools available for the AI assistant:

### `list_coupons`

List discount coupons with optional filters.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `active_only` | boolean | No | Only show active coupons |
| `limit` | integer | No | Max results (default 20) |

### `create_coupon`

Create a new discount coupon.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | string | Yes | Coupon code |
| `name` | string | Yes | Coupon name/description |
| `discount_type` | string | Yes | Type: percentage, fixed, buy_x_get_y |
| `discount_value` | string | Yes | Discount value (% or amount) |
| `usage_limit` | integer | No | Max total uses (0=unlimited) |
| `valid_from` | string | No | Start date (YYYY-MM-DD) |
| `valid_until` | string | No | End date (YYYY-MM-DD) |
| `min_purchase` | string | No | Minimum purchase amount |

### `list_promotions`

List active promotions.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `active_only` | boolean | No | Only show active promotions |

## File Structure

```
README.md
__init__.py
ai_tools.py
apps.py
discounts
forms.py
locale/
  es/
    LC_MESSAGES/
      django.po
migrations/
  0001_initial.py
  __init__.py
models.py
module.py
services/
  __init__.py
  discount_service.py
static/
  icons/
    ion/
templates/
  discounts/
    pages/
      coupon_add.html
      coupon_detail.html
      coupon_edit.html
      coupons.html
      promotion_add.html
      promotion_detail.html
      promotion_edit.html
      promotions.html
      settings.html
      usage.html
    partials/
      coupon_add_content.html
      coupon_detail.html
      coupon_edit_content.html
      coupons_content.html
      coupons_list.html
      panel_coupon_add.html
      panel_coupon_edit.html
      panel_promotion_add.html
      panel_promotion_edit.html
      promotion_add_content.html
      promotion_detail.html
      promotion_edit_content.html
      promotions_content.html
      promotions_list.html
      settings_content.html
      usage_report.html
tests/
  __init__.py
  conftest.py
  test_models.py
  test_service.py
  test_views.py
urls.py
views.py
```
