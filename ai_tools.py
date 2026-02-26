"""AI tools for the Discounts module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class ListCoupons(AssistantTool):
    name = "list_coupons"
    description = "List discount coupons with optional filters."
    module_id = "discounts"
    required_permission = "discounts.view_coupon"
    parameters = {
        "type": "object",
        "properties": {
            "active_only": {"type": "boolean", "description": "Only show active coupons"},
            "limit": {"type": "integer", "description": "Max results (default 20)"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from discounts.models import Coupon
        qs = Coupon.objects.all().order_by('-created_at')
        if args.get('active_only'):
            qs = qs.filter(is_active=True)
        limit = args.get('limit', 20)
        return {
            "coupons": [
                {
                    "id": str(c.id),
                    "code": c.code,
                    "name": c.name,
                    "discount_type": c.discount_type,
                    "discount_value": str(c.discount_value),
                    "usage_count": c.usage_count,
                    "usage_limit": c.usage_limit,
                    "valid_from": str(c.valid_from) if c.valid_from else None,
                    "valid_until": str(c.valid_until) if c.valid_until else None,
                    "is_active": c.is_active,
                }
                for c in qs[:limit]
            ],
            "total": qs.count(),
        }


@register_tool
class CreateCoupon(AssistantTool):
    name = "create_coupon"
    description = "Create a new discount coupon."
    module_id = "discounts"
    required_permission = "discounts.change_coupon"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Coupon code"},
            "name": {"type": "string", "description": "Coupon name/description"},
            "discount_type": {"type": "string", "description": "Type: percentage, fixed, buy_x_get_y"},
            "discount_value": {"type": "string", "description": "Discount value (% or amount)"},
            "usage_limit": {"type": "integer", "description": "Max total uses (0=unlimited)"},
            "valid_from": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "valid_until": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "min_purchase": {"type": "string", "description": "Minimum purchase amount"},
        },
        "required": ["code", "name", "discount_type", "discount_value"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from decimal import Decimal
        from discounts.models import Coupon
        c = Coupon.objects.create(
            code=args['code'].upper(),
            name=args['name'],
            discount_type=args['discount_type'],
            discount_value=Decimal(args['discount_value']),
            usage_limit=args.get('usage_limit', 0),
            valid_from=args.get('valid_from'),
            valid_until=args.get('valid_until'),
            min_purchase=Decimal(args['min_purchase']) if args.get('min_purchase') else None,
            is_active=True,
        )
        return {"id": str(c.id), "code": c.code, "created": True}


@register_tool
class ListPromotions(AssistantTool):
    name = "list_promotions"
    description = "List active promotions."
    module_id = "discounts"
    required_permission = "discounts.view_coupon"
    parameters = {
        "type": "object",
        "properties": {
            "active_only": {"type": "boolean", "description": "Only show active promotions"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from discounts.models import Promotion
        qs = Promotion.objects.all().order_by('-valid_from')
        if args.get('active_only'):
            qs = qs.filter(is_active=True)
        return {
            "promotions": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "discount_type": p.discount_type,
                    "discount_value": str(p.discount_value),
                    "scope": p.scope,
                    "valid_from": str(p.valid_from) if p.valid_from else None,
                    "valid_until": str(p.valid_until) if p.valid_until else None,
                    "is_active": p.is_active,
                }
                for p in qs[:20]
            ]
        }
