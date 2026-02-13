"""
Discounts Module Configuration

This file defines the module metadata and navigation for the Discounts module.
Promotions, coupons, and discount management for POS.
Used by the @module_view decorator to automatically render navigation tabs.
"""
from django.utils.translation import gettext_lazy as _

# Module Identification
MODULE_ID = "discounts"
MODULE_NAME = _("Discounts")
MODULE_ICON = "pricetag-outline"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "sales"

# Target Industries (business verticals this module is designed for)
MODULE_INDUSTRIES = [
    "retail",    # Retail stores
    "restaurant",# Restaurants
    "bar",       # Bars & pubs
    "cafe",      # Cafes & bakeries
    "beauty",    # Beauty & wellness
    "ecommerce", # E-commerce
]

# Sidebar Menu Configuration
MENU = {
    "label": _("Discounts"),
    "icon": "pricetag-outline",
    "order": 35,
    "show": True,
}

# Internal Navigation (Tabs)
NAVIGATION = [
    {
        "id": "dashboard",
        "label": _("Overview"),
        "icon": "grid-outline",
        "view": "",
    },
    {
        "id": "promotions",
        "label": _("Promotions"),
        "icon": "megaphone-outline",
        "view": "promotions",
    },
    {
        "id": "coupons",
        "label": _("Coupons"),
        "icon": "ticket-outline",
        "view": "coupons",
    },
    {
        "id": "settings",
        "label": _("Settings"),
        "icon": "settings-outline",
        "view": "settings",
    },
]

# Module Dependencies
DEPENDENCIES = ['inventory', 'sales', 'customers']

# Default Settings
SETTINGS = {
    "enable_coupons": True,
    "enable_promotions": True,
    "enable_loyalty_discounts": False,
    "max_discount_percent": 100,
    "allow_stacking": False,
}

# Permissions
PERMISSIONS = [
    "discounts.view_discount",
    "discounts.add_discount",
    "discounts.change_discount",
    "discounts.delete_discount",
    "discounts.view_coupon",
    "discounts.add_coupon",
    "discounts.change_coupon",
    "discounts.delete_coupon",
    "discounts.view_promotion",
    "discounts.add_promotion",
    "discounts.change_promotion",
    "discounts.delete_promotion",
]
