"""
Views for Discounts module.

Provides management interface for coupons and promotions.
"""

import json
from datetime import datetime
from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.decorators import login_required

from apps.core.htmx import htmx_view

from .models import Coupon, Promotion, DiscountType, DiscountScope
from .services.discount_service import get_discount_service


# ==============================================================================
# COUPON VIEWS
# ==============================================================================

@login_required
@htmx_view('discounts/coupons/list.html', 'discounts/coupons/partials/list.html')
def coupon_list(request):
    """List all coupons."""
    coupons = Coupon.objects.all().order_by('-created_at')

    # Filter by status
    status = request.GET.get('status')
    if status == 'active':
        coupons = coupons.filter(is_active=True)
    elif status == 'inactive':
        coupons = coupons.filter(is_active=False)

    return {
        'coupons': coupons,
        'status_filter': status,
    }


@login_required
@htmx_view('discounts/coupons/detail.html', 'discounts/coupons/partials/detail.html')
def coupon_detail(request, coupon_id):
    """View coupon details."""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    return {'coupon': coupon}


@login_required
@htmx_view('discounts/coupons/form.html', 'discounts/coupons/partials/form.html')
def coupon_create(request):
    """Create a new coupon."""
    if request.method == 'POST':
        return _save_coupon(request)

    return {
        'coupon': None,
        'discount_types': DiscountType.choices,
        'discount_scopes': DiscountScope.choices,
    }


@login_required
@htmx_view('discounts/coupons/form.html', 'discounts/coupons/partials/form.html')
def coupon_edit(request, coupon_id):
    """Edit an existing coupon."""
    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == 'POST':
        return _save_coupon(request, coupon)

    return {
        'coupon': coupon,
        'discount_types': DiscountType.choices,
        'discount_scopes': DiscountScope.choices,
    }


def _save_coupon(request, coupon=None):
    """Save coupon from POST data."""
    data = request.POST
    is_new = coupon is None

    if is_new:
        coupon = Coupon()

    # Required fields
    coupon.code = data.get('code', '').strip().upper()
    coupon.name = data.get('name', '').strip()
    coupon.discount_type = data.get('discount_type', DiscountType.PERCENTAGE)
    coupon.discount_value = Decimal(data.get('discount_value', '0'))
    coupon.scope = data.get('scope', DiscountScope.ENTIRE_ORDER)

    # Optional fields
    coupon.description = data.get('description', '').strip()
    if data.get('minimum_purchase'):
        coupon.minimum_purchase = Decimal(data['minimum_purchase'])
    if data.get('maximum_discount'):
        coupon.maximum_discount = Decimal(data['maximum_discount'])
    if data.get('max_uses'):
        coupon.max_uses = int(data['max_uses'])
    coupon.max_uses_per_customer = int(data.get('max_uses_per_customer', 1))

    # Validity dates
    if data.get('valid_from'):
        coupon.valid_from = datetime.fromisoformat(data['valid_from'])
    if data.get('valid_until'):
        coupon.valid_until = datetime.fromisoformat(data['valid_until'])

    coupon.is_active = data.get('is_active') == 'on'

    coupon.save()

    return {
        'coupon': coupon,
        'saved': True,
        'discount_types': DiscountType.choices,
        'discount_scopes': DiscountScope.choices,
    }


@login_required
@require_POST
def coupon_delete(request, coupon_id):
    """Delete a coupon."""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def coupon_toggle(request, coupon_id):
    """Toggle coupon active status."""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.is_active = not coupon.is_active
    coupon.save(update_fields=['is_active', 'updated_at'])
    return JsonResponse({
        'success': True,
        'is_active': coupon.is_active
    })


# ==============================================================================
# PROMOTION VIEWS
# ==============================================================================

@login_required
@htmx_view('discounts/promotions/list.html', 'discounts/promotions/partials/list.html')
def promotion_list(request):
    """List all promotions."""
    promotions = Promotion.objects.all().order_by('-priority', '-created_at')

    status = request.GET.get('status')
    if status == 'active':
        promotions = promotions.filter(is_active=True)
    elif status == 'inactive':
        promotions = promotions.filter(is_active=False)

    return {
        'promotions': promotions,
        'status_filter': status,
    }


@login_required
@htmx_view('discounts/promotions/detail.html', 'discounts/promotions/partials/detail.html')
def promotion_detail(request, promotion_id):
    """View promotion details."""
    promotion = get_object_or_404(Promotion, id=promotion_id)
    return {'promotion': promotion}


@login_required
@htmx_view('discounts/promotions/form.html', 'discounts/promotions/partials/form.html')
def promotion_create(request):
    """Create a new promotion."""
    if request.method == 'POST':
        return _save_promotion(request)

    return {
        'promotion': None,
        'discount_types': DiscountType.choices,
        'discount_scopes': DiscountScope.choices,
    }


@login_required
@htmx_view('discounts/promotions/form.html', 'discounts/promotions/partials/form.html')
def promotion_edit(request, promotion_id):
    """Edit an existing promotion."""
    promotion = get_object_or_404(Promotion, id=promotion_id)

    if request.method == 'POST':
        return _save_promotion(request, promotion)

    return {
        'promotion': promotion,
        'discount_types': DiscountType.choices,
        'discount_scopes': DiscountScope.choices,
    }


def _save_promotion(request, promotion=None):
    """Save promotion from POST data."""
    data = request.POST
    is_new = promotion is None

    if is_new:
        promotion = Promotion()

    # Required fields
    promotion.name = data.get('name', '').strip()
    promotion.discount_type = data.get('discount_type', DiscountType.PERCENTAGE)
    promotion.discount_value = Decimal(data.get('discount_value', '0'))
    promotion.scope = data.get('scope', DiscountScope.ENTIRE_ORDER)
    promotion.valid_from = datetime.fromisoformat(data['valid_from'])
    promotion.valid_until = datetime.fromisoformat(data['valid_until'])

    # Optional fields
    promotion.description = data.get('description', '').strip()
    if data.get('minimum_purchase'):
        promotion.minimum_purchase = Decimal(data['minimum_purchase'])
    if data.get('maximum_discount'):
        promotion.maximum_discount = Decimal(data['maximum_discount'])

    promotion.priority = int(data.get('priority', 0))
    promotion.stackable = data.get('stackable') == 'on'
    promotion.is_active = data.get('is_active') == 'on'

    # Schedule
    promotion.days_of_week = data.get('days_of_week', '')
    if data.get('start_time'):
        promotion.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
    if data.get('end_time'):
        promotion.end_time = datetime.strptime(data['end_time'], '%H:%M').time()

    promotion.save()

    return {
        'promotion': promotion,
        'saved': True,
        'discount_types': DiscountType.choices,
        'discount_scopes': DiscountScope.choices,
    }


@login_required
@require_POST
def promotion_delete(request, promotion_id):
    """Delete a promotion."""
    promotion = get_object_or_404(Promotion, id=promotion_id)
    promotion.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def promotion_toggle(request, promotion_id):
    """Toggle promotion active status."""
    promotion = get_object_or_404(Promotion, id=promotion_id)
    promotion.is_active = not promotion.is_active
    promotion.save(update_fields=['is_active', 'updated_at'])
    return JsonResponse({
        'success': True,
        'is_active': promotion.is_active
    })


# ==============================================================================
# API ENDPOINTS (for POS integration)
# ==============================================================================

@login_required
@require_GET
def api_validate_coupon(request):
    """
    Validate a coupon code.

    GET params:
        code: Coupon code
        total: Order total (optional)
        customer_id: Customer ID (optional)
    """
    code = request.GET.get('code', '')
    total = Decimal(request.GET.get('total', '0'))
    customer_id = request.GET.get('customer_id')

    service = get_discount_service()
    is_valid, message, coupon = service.validate_coupon(code, total, customer_id)

    if not is_valid:
        return JsonResponse({
            'valid': False,
            'message': message
        })

    discount_amount = coupon.calculate_discount(total)
    return JsonResponse({
        'valid': True,
        'coupon_id': str(coupon.id),
        'coupon_name': coupon.name,
        'discount_type': coupon.discount_type,
        'discount_value': str(coupon.discount_value),
        'discount_amount': str(discount_amount),
        'message': f"Save {discount_amount}!"
    })


@login_required
@require_GET
def api_active_promotions(request):
    """Get currently active promotions."""
    service = get_discount_service()
    promotions = service.get_active_promotions()

    return JsonResponse({
        'promotions': [
            {
                'id': str(p.id),
                'name': p.name,
                'description': p.description,
                'discount_type': p.discount_type,
                'discount_value': str(p.discount_value),
                'scope': p.scope,
                'stackable': p.stackable,
            }
            for p in promotions
        ]
    })


@login_required
@require_POST
def api_calculate_discounts(request):
    """
    Calculate all applicable discounts for an order.

    POST body (JSON):
        total: Order total
        coupon_code: Optional coupon code
        customer_id: Optional customer ID
        product_ids: Optional list of product IDs
        category_ids: Optional list of category IDs
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    total = Decimal(str(data.get('total', '0')))
    coupon_code = data.get('coupon_code')
    customer_id = data.get('customer_id')
    product_ids = data.get('product_ids', [])
    category_ids = data.get('category_ids', [])

    service = get_discount_service()
    result = service.calculate_order_discounts(
        order_total=total,
        coupon_code=coupon_code,
        customer_id=customer_id,
        product_ids=product_ids,
        category_ids=category_ids
    )

    return JsonResponse({
        'original_total': str(result.original_total),
        'discounted_total': str(result.discounted_total),
        'total_discount': str(result.total_discount),
        'applied_discounts': [
            {
                'source': d.source,
                'source_id': d.source_id,
                'source_name': d.source_name,
                'discount_type': d.discount_type,
                'discount_value': str(d.discount_value),
                'discount_amount': str(d.discount_amount),
            }
            for d in result.applied_discounts
        ],
        'errors': result.errors
    })
