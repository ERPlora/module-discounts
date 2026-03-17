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


@register_tool
class UpdateDiscount(AssistantTool):
    name = "update_discount"
    description = "Update an existing coupon's fields."
    module_id = "discounts"
    required_permission = "discounts.change_coupon"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "coupon_id": {"type": "string", "description": "Coupon ID"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "discount_type": {"type": "string", "description": "percentage, fixed, buy_x_get_y"},
            "discount_value": {"type": "string"},
            "scope": {"type": "string", "description": "order, products, categories"},
            "min_purchase": {"type": "string"},
            "max_discount": {"type": "string"},
            "usage_limit": {"type": "integer"},
            "usage_per_customer": {"type": "integer"},
            "valid_from": {"type": "string", "description": "Datetime (YYYY-MM-DD or YYYY-MM-DD HH:MM)"},
            "valid_until": {"type": "string", "description": "Datetime (YYYY-MM-DD or YYYY-MM-DD HH:MM)"},
            "priority": {"type": "integer"},
            "stackable": {"type": "boolean"},
            "is_active": {"type": "boolean"},
        },
        "required": ["coupon_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from decimal import Decimal
        from discounts.models import Coupon
        try:
            c = Coupon.objects.get(id=args['coupon_id'])
        except Coupon.DoesNotExist:
            return {"error": f"Coupon {args['coupon_id']} not found"}
        fields = ['updated_at']
        for field in ('name', 'description', 'discount_type', 'scope'):
            if field in args:
                setattr(c, field, args[field])
                fields.append(field)
        for dec_field in ('discount_value', 'min_purchase', 'max_discount'):
            if dec_field in args:
                setattr(c, dec_field, Decimal(args[dec_field]) if args[dec_field] else None)
                fields.append(dec_field)
        for int_field in ('usage_limit', 'usage_per_customer', 'priority'):
            if int_field in args:
                setattr(c, int_field, args[int_field])
                fields.append(int_field)
        for bool_field in ('stackable', 'is_active'):
            if bool_field in args:
                setattr(c, bool_field, args[bool_field])
                fields.append(bool_field)
        for dt_field in ('valid_from', 'valid_until'):
            if dt_field in args:
                setattr(c, dt_field, args[dt_field])
                fields.append(dt_field)
        c.save(update_fields=fields)
        return {"id": str(c.id), "code": c.code, "updated": True}


@register_tool
class DeleteDiscount(AssistantTool):
    name = "delete_discount"
    description = "Delete a coupon by ID."
    module_id = "discounts"
    required_permission = "discounts.change_coupon"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "coupon_id": {"type": "string", "description": "Coupon ID"},
        },
        "required": ["coupon_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from discounts.models import Coupon
        try:
            c = Coupon.objects.get(id=args['coupon_id'])
            code = c.code
            c.delete()
            return {"deleted": True, "code": code}
        except Coupon.DoesNotExist:
            return {"error": f"Coupon {args['coupon_id']} not found"}


@register_tool
class BulkCreateDiscounts(AssistantTool):
    name = "bulk_create_discounts"
    description = "Create multiple discount coupons at once (max 50)."
    module_id = "discounts"
    required_permission = "discounts.change_coupon"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "coupons": {
                "type": "array",
                "description": "List of coupons to create (max 50)",
                "items": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "name": {"type": "string"},
                        "discount_type": {"type": "string", "description": "percentage, fixed, buy_x_get_y"},
                        "discount_value": {"type": "string"},
                        "usage_limit": {"type": "integer"},
                        "valid_from": {"type": "string"},
                        "valid_until": {"type": "string"},
                        "min_purchase": {"type": "string"},
                    },
                    "required": ["code", "name", "discount_type", "discount_value"],
                    "additionalProperties": False,
                },
                "maxItems": 50,
            },
        },
        "required": ["coupons"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from decimal import Decimal
        from discounts.models import Coupon
        created = []
        for item in args['coupons'][:50]:
            c = Coupon.objects.create(
                code=item['code'].upper(),
                name=item['name'],
                discount_type=item['discount_type'],
                discount_value=Decimal(item['discount_value']),
                usage_limit=item.get('usage_limit'),
                valid_from=item.get('valid_from'),
                valid_until=item.get('valid_until'),
                min_purchase=Decimal(item['min_purchase']) if item.get('min_purchase') else Decimal('0.00'),
                is_active=True,
            )
            created.append({"id": str(c.id), "code": c.code})
        return {"created": created, "count": len(created)}
