"""
Discounts Module Views

Coupon and promotion management with datatable pattern, side panel CRUD,
usage reporting, and POS API endpoints.
"""
import json
from datetime import datetime
from decimal import Decimal

from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render as django_render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST, require_GET

from apps.accounts.decorators import login_required
from apps.core.htmx import htmx_view
from apps.core.services import export_to_csv, export_to_excel
from apps.modules_runtime.navigation import with_module_nav

from .models import (
    Coupon, Promotion, DiscountCondition, DiscountUsage,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PER_PAGE_CHOICES = [10, 25, 50, 100]

COUPON_SORT_FIELDS = {
    'code': 'code',
    'name': 'name',
    'created': 'created_at',
    'value': 'discount_value',
}

PROMOTION_SORT_FIELDS = {
    'name': 'name',
    'priority': 'priority',
    'created': 'created_at',
    'value': 'discount_value',
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hub_id(request):
    return request.session.get('hub_id')


def _render_coupon_list(request, hub):
    """Render the coupons list partial after a mutation."""
    coupons = Coupon.objects.filter(hub_id=hub, is_deleted=False).order_by('-created_at')
    paginator = Paginator(coupons, 10)
    page_obj = paginator.get_page(1)
    return django_render(request, 'discounts/partials/coupons_list.html', {
        'coupons': page_obj,
        'page_obj': page_obj,
        'search': '',
        'sort_field': 'created',
        'sort_dir': 'desc',
        'status_filter': '',
        'per_page': 10,
    })


def _render_promotion_list(request, hub):
    """Render the promotions list partial after a mutation."""
    promotions = Promotion.objects.filter(hub_id=hub, is_deleted=False).order_by('-priority', '-created_at')
    paginator = Paginator(promotions, 10)
    page_obj = paginator.get_page(1)
    return django_render(request, 'discounts/partials/promotions_list.html', {
        'promotions': page_obj,
        'page_obj': page_obj,
        'search': '',
        'sort_field': 'name',
        'sort_dir': 'asc',
        'status_filter': '',
        'per_page': 10,
    })


def _save_coupon_from_post(request, coupon):
    """Populate a Coupon instance from POST data and save it."""
    data = request.POST
    coupon.code = data.get('code', '').strip().upper()
    coupon.name = data.get('name', '').strip()
    coupon.description = data.get('description', '').strip()
    coupon.discount_type = data.get('discount_type', 'percentage')
    coupon.discount_value = Decimal(data.get('discount_value', '0'))
    coupon.scope = data.get('scope', 'order')
    coupon.min_purchase = Decimal(data.get('min_purchase', '0') or '0')

    if data.get('max_discount'):
        coupon.max_discount = Decimal(data['max_discount'])
    else:
        coupon.max_discount = None

    if data.get('usage_limit'):
        coupon.usage_limit = int(data['usage_limit'])
    else:
        coupon.usage_limit = None

    coupon.usage_per_customer = int(data.get('usage_per_customer', '1') or '1')

    if data.get('valid_from'):
        coupon.valid_from = datetime.fromisoformat(data['valid_from'])
    if data.get('valid_until'):
        coupon.valid_until = datetime.fromisoformat(data['valid_until'])
    else:
        coupon.valid_until = None

    coupon.priority = int(data.get('priority', '0') or '0')
    coupon.stackable = data.get('stackable') == 'on'
    coupon.is_active = data.get('is_active') == 'on'

    if data.get('buy_quantity'):
        coupon.buy_quantity = int(data['buy_quantity'])
    if data.get('get_quantity'):
        coupon.get_quantity = int(data['get_quantity'])
    if data.get('get_discount_percent'):
        coupon.get_discount_percent = Decimal(data['get_discount_percent'])

    coupon.save()


def _save_promotion_from_post(request, promotion):
    """Populate a Promotion instance from POST data and save it."""
    data = request.POST
    promotion.name = data.get('name', '').strip()
    promotion.description = data.get('description', '').strip()
    promotion.discount_type = data.get('discount_type', 'percentage')
    promotion.discount_value = Decimal(data.get('discount_value', '0'))
    promotion.scope = data.get('scope', 'order')

    if data.get('min_purchase'):
        promotion.min_purchase = Decimal(data['min_purchase'])
    else:
        promotion.min_purchase = None

    if data.get('max_discount'):
        promotion.max_discount = Decimal(data['max_discount'])
    else:
        promotion.max_discount = None

    promotion.valid_from = datetime.fromisoformat(data['valid_from'])
    promotion.valid_until = datetime.fromisoformat(data['valid_until'])

    promotion.days_of_week = data.get('days_of_week', '')
    if data.get('start_time'):
        promotion.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
    else:
        promotion.start_time = None
    if data.get('end_time'):
        promotion.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    else:
        promotion.end_time = None

    promotion.priority = int(data.get('priority', '0') or '0')
    promotion.stackable = data.get('stackable') == 'on'
    promotion.is_active = data.get('is_active') == 'on'

    if data.get('buy_quantity'):
        promotion.buy_quantity = int(data['buy_quantity'])
    if data.get('get_quantity'):
        promotion.get_quantity = int(data['get_quantity'])
    if data.get('get_discount_percent'):
        promotion.get_discount_percent = Decimal(data['get_discount_percent'])

    promotion.save()


# ============================================================================
# Coupon views
# ============================================================================

@login_required
@with_module_nav('discounts', 'coupons')
@htmx_view('discounts/pages/coupons.html', 'discounts/partials/coupons_content.html')
def coupon_list(request):
    """Coupons datatable with search, sort, filter, pagination and export."""
    hub = _hub_id(request)
    search = request.GET.get('q', '').strip()
    sort_field = request.GET.get('sort', 'created')
    sort_dir = request.GET.get('dir', 'desc')
    status_filter = request.GET.get('status', '')
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 10))
    if per_page not in PER_PAGE_CHOICES:
        per_page = 10

    coupons = Coupon.objects.filter(hub_id=hub, is_deleted=False)

    # Search
    if search:
        coupons = coupons.filter(
            Q(name__icontains=search) | Q(code__icontains=search)
        )

    # Status filter
    if status_filter == 'active':
        coupons = coupons.filter(is_active=True)
    elif status_filter == 'inactive':
        coupons = coupons.filter(is_active=False)

    # Sort
    order_by = COUPON_SORT_FIELDS.get(sort_field, 'created_at')
    if sort_dir == 'desc':
        order_by = f'-{order_by}'
    coupons = coupons.order_by(order_by)

    # Export (before pagination -- exports all filtered results)
    export_format = request.GET.get('export')
    if export_format in ('csv', 'excel'):
        export_fields = [
            'code', 'name', 'discount_type', 'discount_value', 'scope',
            'usage_count', 'usage_limit', 'valid_from', 'valid_until', 'is_active',
        ]
        export_headers = [
            str(_('Code')), str(_('Name')), str(_('Discount Type')),
            str(_('Discount Value')), str(_('Scope')), str(_('Usage Count')),
            str(_('Usage Limit')), str(_('Valid From')), str(_('Valid Until')),
            str(_('Status')),
        ]
        export_formatters = {
            'is_active': lambda v: str(_('Active')) if v else str(_('Inactive')),
            'valid_from': lambda v: v.strftime('%Y-%m-%d %H:%M') if v else '',
            'valid_until': lambda v: v.strftime('%Y-%m-%d %H:%M') if v else '',
        }
        if export_format == 'csv':
            return export_to_csv(
                coupons,
                fields=export_fields,
                headers=export_headers,
                field_formatters=export_formatters,
                filename='coupons.csv',
            )
        return export_to_excel(
            coupons,
            fields=export_fields,
            headers=export_headers,
            field_formatters=export_formatters,
            filename='coupons.xlsx',
            sheet_name=str(_('Coupons')),
        )

    # Pagination
    paginator = Paginator(coupons, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'coupons': page_obj,
        'page_obj': page_obj,
        'search': search,
        'sort_field': sort_field,
        'sort_dir': sort_dir,
        'status_filter': status_filter,
        'per_page': per_page,
    }

    # HTMX partial: swap only datatable body (search, sort, filter, paginate)
    if request.htmx and request.htmx.target == 'datatable-body':
        return django_render(request, 'discounts/partials/coupons_list.html', context)

    return context


@login_required
@with_module_nav('discounts', 'coupons')
@htmx_view('discounts/pages/coupon_detail.html', 'discounts/partials/coupon_detail.html')
def coupon_detail(request, coupon_id):
    """Coupon detail page with conditions and usage history."""
    hub = _hub_id(request)
    coupon = get_object_or_404(Coupon, id=coupon_id, hub_id=hub, is_deleted=False)
    conditions = coupon.conditions.filter(is_deleted=False)
    recent_usages = coupon.usages.filter(is_deleted=False).order_by('-used_at')[:10]
    total_savings = coupon.usages.filter(is_deleted=False).aggregate(
        total=Sum('amount_discounted')
    )['total'] or Decimal('0.00')

    return {
        'coupon': coupon,
        'conditions': conditions,
        'recent_usages': recent_usages,
        'total_savings': total_savings,
    }


@login_required
def coupon_create(request):
    """Add coupon -- renders side panel via HTMX."""
    hub = _hub_id(request)

    if request.method == 'POST':
        coupon = Coupon(hub_id=hub)
        _save_coupon_from_post(request, coupon)
        messages.success(request, _('Coupon created successfully'))
        return _render_coupon_list(request, hub)

    # GET: render panel form
    return django_render(request, 'discounts/partials/panel_coupon_add.html', {
        'discount_types': Coupon.DISCOUNT_TYPES,
        'scope_choices': Coupon.SCOPE_CHOICES,
    })


@login_required
def coupon_edit(request, coupon_id):
    """Edit coupon -- renders side panel via HTMX."""
    hub = _hub_id(request)
    coupon = get_object_or_404(Coupon, id=coupon_id, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        _save_coupon_from_post(request, coupon)
        messages.success(request, _('Coupon updated successfully'))
        return _render_coupon_list(request, hub)

    # GET: render panel form
    return django_render(request, 'discounts/partials/panel_coupon_edit.html', {
        'coupon': coupon,
        'discount_types': Coupon.DISCOUNT_TYPES,
        'scope_choices': Coupon.SCOPE_CHOICES,
    })


@login_required
@require_POST
def coupon_delete(request, coupon_id):
    """Soft-delete a coupon and return the updated list partial."""
    hub = _hub_id(request)
    coupon = get_object_or_404(Coupon, id=coupon_id, hub_id=hub, is_deleted=False)
    coupon.is_deleted = True
    coupon.deleted_at = timezone.now()
    coupon.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    messages.success(request, _('Coupon deleted successfully'))
    return _render_coupon_list(request, hub)


@login_required
@require_POST
def coupon_toggle(request, coupon_id):
    """Toggle coupon active status and return the updated list partial."""
    hub = _hub_id(request)
    coupon = get_object_or_404(Coupon, id=coupon_id, hub_id=hub, is_deleted=False)
    coupon.is_active = not coupon.is_active
    coupon.save(update_fields=['is_active', 'updated_at'])
    status = _('activated') if coupon.is_active else _('deactivated')
    messages.success(request, _('Coupon %(status)s successfully') % {'status': status})
    return _render_coupon_list(request, hub)


# ============================================================================
# Promotion views
# ============================================================================

@login_required
@with_module_nav('discounts', 'promotions')
@htmx_view('discounts/pages/promotions.html', 'discounts/partials/promotions_content.html')
def promotion_list(request):
    """Promotions datatable with search, sort, filter, pagination and export."""
    hub = _hub_id(request)
    search = request.GET.get('q', '').strip()
    sort_field = request.GET.get('sort', 'name')
    sort_dir = request.GET.get('dir', 'asc')
    status_filter = request.GET.get('status', '')
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 10))
    if per_page not in PER_PAGE_CHOICES:
        per_page = 10

    promotions = Promotion.objects.filter(hub_id=hub, is_deleted=False)

    # Search
    if search:
        promotions = promotions.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    # Status filter
    if status_filter == 'active':
        promotions = promotions.filter(is_active=True)
    elif status_filter == 'inactive':
        promotions = promotions.filter(is_active=False)

    # Sort
    order_by = PROMOTION_SORT_FIELDS.get(sort_field, 'name')
    if sort_dir == 'desc':
        order_by = f'-{order_by}'
    promotions = promotions.order_by(order_by)

    # Export (before pagination -- exports all filtered results)
    export_format = request.GET.get('export')
    if export_format in ('csv', 'excel'):
        export_fields = [
            'name', 'discount_type', 'discount_value', 'scope',
            'valid_from', 'valid_until', 'priority', 'stackable', 'is_active',
        ]
        export_headers = [
            str(_('Name')), str(_('Discount Type')), str(_('Discount Value')),
            str(_('Scope')), str(_('Valid From')), str(_('Valid Until')),
            str(_('Priority')), str(_('Stackable')), str(_('Status')),
        ]
        export_formatters = {
            'is_active': lambda v: str(_('Active')) if v else str(_('Inactive')),
            'stackable': lambda v: str(_('Yes')) if v else str(_('No')),
            'valid_from': lambda v: v.strftime('%Y-%m-%d %H:%M') if v else '',
            'valid_until': lambda v: v.strftime('%Y-%m-%d %H:%M') if v else '',
        }
        if export_format == 'csv':
            return export_to_csv(
                promotions,
                fields=export_fields,
                headers=export_headers,
                field_formatters=export_formatters,
                filename='promotions.csv',
            )
        return export_to_excel(
            promotions,
            fields=export_fields,
            headers=export_headers,
            field_formatters=export_formatters,
            filename='promotions.xlsx',
            sheet_name=str(_('Promotions')),
        )

    # Pagination
    paginator = Paginator(promotions, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'promotions': page_obj,
        'page_obj': page_obj,
        'search': search,
        'sort_field': sort_field,
        'sort_dir': sort_dir,
        'status_filter': status_filter,
        'per_page': per_page,
    }

    # HTMX partial: swap only datatable body (search, sort, filter, paginate)
    if request.htmx and request.htmx.target == 'datatable-body':
        return django_render(request, 'discounts/partials/promotions_list.html', context)

    return context


@login_required
@with_module_nav('discounts', 'promotions')
@htmx_view('discounts/pages/promotion_detail.html', 'discounts/partials/promotion_detail.html')
def promotion_detail(request, promotion_id):
    """Promotion detail page with conditions and usage history."""
    hub = _hub_id(request)
    promotion = get_object_or_404(Promotion, id=promotion_id, hub_id=hub, is_deleted=False)
    conditions = promotion.conditions.filter(is_deleted=False)
    recent_usages = promotion.usages.filter(is_deleted=False).order_by('-used_at')[:10]

    return {
        'promotion': promotion,
        'conditions': conditions,
        'recent_usages': recent_usages,
    }


@login_required
def promotion_create(request):
    """Add promotion -- renders side panel via HTMX."""
    hub = _hub_id(request)

    if request.method == 'POST':
        promotion = Promotion(hub_id=hub)
        _save_promotion_from_post(request, promotion)
        messages.success(request, _('Promotion created successfully'))
        return _render_promotion_list(request, hub)

    # GET: render panel form
    return django_render(request, 'discounts/partials/panel_promotion_add.html', {
        'discount_types': Promotion.DISCOUNT_TYPES,
        'scope_choices': Promotion.SCOPE_CHOICES,
    })


@login_required
def promotion_edit(request, promotion_id):
    """Edit promotion -- renders side panel via HTMX."""
    hub = _hub_id(request)
    promotion = get_object_or_404(Promotion, id=promotion_id, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        _save_promotion_from_post(request, promotion)
        messages.success(request, _('Promotion updated successfully'))
        return _render_promotion_list(request, hub)

    # GET: render panel form
    return django_render(request, 'discounts/partials/panel_promotion_edit.html', {
        'promotion': promotion,
        'discount_types': Promotion.DISCOUNT_TYPES,
        'scope_choices': Promotion.SCOPE_CHOICES,
    })


@login_required
@require_POST
def promotion_delete(request, promotion_id):
    """Soft-delete a promotion and return the updated list partial."""
    hub = _hub_id(request)
    promotion = get_object_or_404(Promotion, id=promotion_id, hub_id=hub, is_deleted=False)
    promotion.is_deleted = True
    promotion.deleted_at = timezone.now()
    promotion.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    messages.success(request, _('Promotion deleted successfully'))
    return _render_promotion_list(request, hub)


@login_required
@require_POST
def promotion_toggle(request, promotion_id):
    """Toggle promotion active status and return the updated list partial."""
    hub = _hub_id(request)
    promotion = get_object_or_404(Promotion, id=promotion_id, hub_id=hub, is_deleted=False)
    promotion.is_active = not promotion.is_active
    promotion.save(update_fields=['is_active', 'updated_at'])
    status = _('activated') if promotion.is_active else _('deactivated')
    messages.success(request, _('Promotion %(status)s successfully') % {'status': status})
    return _render_promotion_list(request, hub)


# ============================================================================
# Condition views
# ============================================================================

@login_required
@require_POST
def condition_add(request, coupon_id=None, promotion_id=None):
    hub = _hub_id(request)

    kwargs = {'hub_id': hub}
    if coupon_id:
        parent = get_object_or_404(Coupon, id=coupon_id, hub_id=hub, is_deleted=False)
        kwargs['coupon'] = parent
    elif promotion_id:
        parent = get_object_or_404(Promotion, id=promotion_id, hub_id=hub, is_deleted=False)
        kwargs['promotion'] = parent

    DiscountCondition.objects.create(
        condition_type=request.POST.get('condition_type', ''),
        value=request.POST.get('value', ''),
        is_inclusive=request.POST.get('is_inclusive') != 'off',
        **kwargs,
    )
    return JsonResponse({'success': True})


@login_required
@require_POST
def condition_delete(request, condition_id):
    hub = _hub_id(request)
    condition = get_object_or_404(DiscountCondition, id=condition_id, hub_id=hub, is_deleted=False)
    condition.is_deleted = True
    condition.deleted_at = timezone.now()
    condition.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


# ============================================================================
# Usage report
# ============================================================================

@login_required
@with_module_nav('discounts', 'dashboard')
@htmx_view('discounts/pages/usage.html', 'discounts/partials/usage_report.html')
def usage_report(request):
    hub = _hub_id(request)
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    usages = DiscountUsage.objects.filter(
        hub_id=hub, is_deleted=False,
    ).select_related('coupon', 'promotion', 'sale', 'customer').order_by('-used_at')

    if date_from:
        usages = usages.filter(used_at__date__gte=date_from)
    if date_to:
        usages = usages.filter(used_at__date__lte=date_to)

    total_usages = usages.count()
    total_savings = usages.aggregate(
        total=Sum('amount_discounted')
    )['total'] or Decimal('0.00')

    return {
        'usages': usages[:100],
        'date_from': date_from,
        'date_to': date_to,
        'total_usages': total_usages,
        'total_savings': total_savings,
    }


# ============================================================================
# API endpoints (POS integration)
# ============================================================================

@login_required
@require_POST
def api_validate_coupon(request):
    hub = _hub_id(request)
    code = request.POST.get('code', '').strip().upper()
    subtotal = Decimal(request.POST.get('subtotal', '0'))

    if not code:
        return JsonResponse({'valid': False, 'message': 'Please enter a coupon code'})

    coupon = Coupon.objects.filter(
        hub_id=hub, code__iexact=code, is_deleted=False,
    ).first()

    if not coupon:
        return JsonResponse({'valid': False, 'message': 'Invalid coupon code'})

    can_use, message = coupon.can_use(order_total=subtotal)
    if not can_use:
        return JsonResponse({'valid': False, 'message': message})

    discount_amount = coupon.calculate_discount(subtotal)
    return JsonResponse({
        'valid': True,
        'coupon_id': str(coupon.id),
        'coupon_name': coupon.name,
        'discount_type': coupon.discount_type,
        'discount_value': str(coupon.discount_value),
        'discount_amount': str(discount_amount),
    })


@login_required
@require_GET
def api_active_promotions(request):
    hub = _hub_id(request)
    promotions = Promotion.objects.filter(
        hub_id=hub, is_active=True, is_deleted=False,
    ).order_by('-priority')

    data = [{
        'id': str(p.id),
        'name': p.name,
        'description': p.description,
        'discount_type': p.discount_type,
        'discount_value': str(p.discount_value),
        'scope': p.scope,
        'stackable': p.stackable,
        'is_valid': p.is_valid,
    } for p in promotions]

    return JsonResponse({'promotions': data})


@login_required
@require_POST
def api_calculate_discounts(request):
    hub = _hub_id(request)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    total = Decimal(str(data.get('total', '0')))
    coupon_code = data.get('coupon_code')

    applied = []
    total_discount = Decimal('0.00')

    # Apply coupon if provided
    if coupon_code:
        coupon = Coupon.objects.filter(
            hub_id=hub, code__iexact=coupon_code, is_deleted=False,
        ).first()
        if coupon:
            can_use, _ = coupon.can_use(order_total=total)
            if can_use:
                discount = coupon.calculate_discount(total)
                total_discount += discount
                applied.append({
                    'source': 'coupon',
                    'source_id': str(coupon.id),
                    'source_name': coupon.name,
                    'discount_amount': str(discount),
                })

    # Apply active promotions
    promotions = Promotion.objects.filter(
        hub_id=hub, is_active=True, is_deleted=False,
    ).order_by('-priority')

    for promo in promotions:
        if not promo.is_valid:
            continue
        discount = promo.calculate_discount(total - total_discount if not promo.stackable else total)
        if discount > 0:
            total_discount += discount
            applied.append({
                'source': 'promotion',
                'source_id': str(promo.id),
                'source_name': promo.name,
                'discount_amount': str(discount),
            })
            if not promo.stackable:
                break

    return JsonResponse({
        'original_total': str(total),
        'discounted_total': str(max(Decimal('0'), total - total_discount)),
        'total_discount': str(total_discount),
        'applied_discounts': applied,
    })


@login_required
@require_POST
def api_apply_discount(request):
    hub = _hub_id(request)
    discount_id = request.POST.get('discount_id')
    discount_source = request.POST.get('source', 'coupon')
    sale_id = request.POST.get('sale_id')
    original_amount = Decimal(request.POST.get('original_amount', '0'))
    discount_amount = Decimal(request.POST.get('discount_amount', '0'))

    kwargs = {'hub_id': hub, 'amount_discounted': discount_amount, 'original_amount': original_amount}

    if sale_id:
        kwargs['sale_id'] = sale_id

    if discount_source == 'coupon':
        coupon = get_object_or_404(Coupon, id=discount_id, hub_id=hub, is_deleted=False)
        kwargs['coupon'] = coupon
        coupon.increment_usage()
    else:
        promotion = get_object_or_404(Promotion, id=discount_id, hub_id=hub, is_deleted=False)
        kwargs['promotion'] = promotion

    DiscountUsage.objects.create(**kwargs)

    return JsonResponse({'success': True})


# ============================================================================
# Settings
# ============================================================================

@login_required
@with_module_nav('discounts', 'settings')
@htmx_view('discounts/pages/settings.html', 'discounts/partials/settings_content.html')
def settings_view(request):
    hub = _hub_id(request)
    total_coupons = Coupon.objects.filter(hub_id=hub, is_deleted=False).count()
    active_coupons = sum(
        1 for c in Coupon.objects.filter(hub_id=hub, is_deleted=False)
        if c.status == 'active'
    )
    total_promotions = Promotion.objects.filter(hub_id=hub, is_deleted=False).count()
    active_promotions = sum(
        1 for p in Promotion.objects.filter(hub_id=hub, is_deleted=False)
        if p.status == 'active'
    )

    return {
        'total_coupons': total_coupons,
        'active_coupons': active_coupons,
        'total_promotions': total_promotions,
        'active_promotions': active_promotions,
    }
