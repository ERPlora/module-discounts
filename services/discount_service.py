"""
Discount Service for ERPlora Hub.

Provides business logic for applying coupons and promotions to orders.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.utils import timezone


@dataclass
class AppliedDiscount:
    """Represents a discount applied to an order."""
    source: str  # 'coupon' or 'promotion'
    source_id: str
    source_name: str
    discount_type: str
    discount_value: Decimal
    discount_amount: Decimal
    original_total: Decimal


@dataclass
class DiscountResult:
    """Result of applying discounts to an order."""
    original_total: Decimal
    discounted_total: Decimal
    total_discount: Decimal
    applied_discounts: list[AppliedDiscount]
    errors: list[str]


# Singleton instance
_discount_service: Optional['DiscountService'] = None


def get_discount_service() -> 'DiscountService':
    """Get or create the singleton DiscountService instance."""
    global _discount_service
    if _discount_service is None:
        _discount_service = DiscountService()
    return _discount_service


class DiscountService:
    """
    Service for managing and applying discounts.

    Handles:
    - Coupon validation and application
    - Promotion detection and application
    - Discount stacking rules
    - Order total calculations
    """

    def __init__(self):
        self._coupon_model = None
        self._promotion_model = None

    @property
    def Coupon(self):
        """Lazy-load Coupon model."""
        if self._coupon_model is None:
            from discounts.models import Coupon
            self._coupon_model = Coupon
        return self._coupon_model

    @property
    def Promotion(self):
        """Lazy-load Promotion model."""
        if self._promotion_model is None:
            from discounts.models import Promotion
            self._promotion_model = Promotion
        return self._promotion_model

    def validate_coupon(
        self,
        code: str,
        order_total: Decimal = Decimal('0'),
        customer_id: str | None = None
    ) -> tuple[bool, str, Optional['Coupon']]:
        """
        Validate a coupon code.

        Args:
            code: Coupon code to validate
            order_total: Current order total
            customer_id: Optional customer identifier

        Returns:
            Tuple of (is_valid, message, coupon_or_none)
        """
        try:
            coupon = self.Coupon.objects.get(code__iexact=code.strip())
        except self.Coupon.DoesNotExist:
            return False, "Invalid coupon code", None

        can_use, reason = coupon.can_use(customer_id, order_total)
        if not can_use:
            return False, reason, None

        return True, "Coupon is valid", coupon

    def apply_coupon(
        self,
        code: str,
        order_total: Decimal,
        customer_id: str | None = None
    ) -> tuple[Decimal, str, Optional['Coupon']]:
        """
        Apply a coupon to an order.

        Args:
            code: Coupon code
            order_total: Order total before discount
            customer_id: Optional customer identifier

        Returns:
            Tuple of (discount_amount, message, coupon_or_none)
        """
        is_valid, message, coupon = self.validate_coupon(code, order_total, customer_id)

        if not is_valid:
            return Decimal('0'), message, None

        discount_amount = coupon.calculate_discount(order_total)
        return discount_amount, f"Coupon applied: -{discount_amount}", coupon

    def get_active_promotions(self) -> list:
        """Get all currently active promotions."""
        now = timezone.now()
        return list(
            self.Promotion.objects.filter(
                is_active=True,
                valid_from__lte=now,
                valid_until__gte=now
            ).order_by('-priority')
        )

    def get_applicable_promotions(
        self,
        order_total: Decimal,
        product_ids: list[str] | None = None,
        category_ids: list[str] | None = None
    ) -> list:
        """
        Get promotions applicable to the current order.

        Args:
            order_total: Current order total
            product_ids: List of product IDs in the order
            category_ids: List of category IDs of products in order

        Returns:
            List of applicable Promotion objects
        """
        from discounts.models import DiscountScope

        active_promotions = self.get_active_promotions()
        applicable = []

        for promo in active_promotions:
            if not promo.is_valid:
                continue

            if promo.minimum_purchase and order_total < promo.minimum_purchase:
                continue

            # Check scope
            if promo.scope == DiscountScope.ENTIRE_ORDER:
                applicable.append(promo)
            elif promo.scope == DiscountScope.SPECIFIC_PRODUCTS and product_ids:
                promo_product_ids = set(
                    promo.products.values_list('product_id', flat=True)
                )
                if promo_product_ids.intersection(set(product_ids)):
                    applicable.append(promo)
            elif promo.scope == DiscountScope.SPECIFIC_CATEGORIES and category_ids:
                promo_category_ids = set(
                    promo.categories.values_list('category_id', flat=True)
                )
                if promo_category_ids.intersection(set(category_ids)):
                    applicable.append(promo)
            elif promo.scope == DiscountScope.MINIMUM_PURCHASE:
                if not promo.minimum_purchase or order_total >= promo.minimum_purchase:
                    applicable.append(promo)

        return applicable

    def calculate_order_discounts(
        self,
        order_total: Decimal,
        coupon_code: str | None = None,
        customer_id: str | None = None,
        product_ids: list[str] | None = None,
        category_ids: list[str] | None = None,
        allow_stacking: bool = False
    ) -> DiscountResult:
        """
        Calculate all applicable discounts for an order.

        Args:
            order_total: Original order total
            coupon_code: Optional coupon code to apply
            customer_id: Optional customer identifier
            product_ids: List of product IDs in order
            category_ids: List of category IDs in order
            allow_stacking: Allow multiple discounts to stack

        Returns:
            DiscountResult with all applied discounts
        """
        from discounts.models import DiscountType

        applied_discounts: list[AppliedDiscount] = []
        errors: list[str] = []
        working_total = order_total
        total_discount = Decimal('0')

        # Apply coupon first (if provided)
        if coupon_code:
            discount_amount, message, coupon = self.apply_coupon(
                coupon_code, order_total, customer_id
            )
            if coupon and discount_amount > 0:
                applied_discounts.append(AppliedDiscount(
                    source='coupon',
                    source_id=str(coupon.id),
                    source_name=coupon.name,
                    discount_type=coupon.discount_type,
                    discount_value=coupon.discount_value,
                    discount_amount=discount_amount,
                    original_total=order_total
                ))
                total_discount += discount_amount
                working_total -= discount_amount

                # If coupon used, don't allow promotion stacking unless explicitly allowed
                if not allow_stacking:
                    return DiscountResult(
                        original_total=order_total,
                        discounted_total=max(Decimal('0'), working_total),
                        total_discount=total_discount,
                        applied_discounts=applied_discounts,
                        errors=errors
                    )
            elif not coupon:
                errors.append(message)

        # Apply promotions
        promotions = self.get_applicable_promotions(
            working_total, product_ids, category_ids
        )

        for promo in promotions:
            if not allow_stacking and applied_discounts and not promo.stackable:
                continue

            discount_amount = promo.calculate_discount(working_total)
            if discount_amount > 0:
                applied_discounts.append(AppliedDiscount(
                    source='promotion',
                    source_id=str(promo.id),
                    source_name=promo.name,
                    discount_type=promo.discount_type,
                    discount_value=promo.discount_value,
                    discount_amount=discount_amount,
                    original_total=working_total
                ))
                total_discount += discount_amount
                working_total -= discount_amount

                # Stop after first non-stackable promotion
                if not promo.stackable:
                    break

        return DiscountResult(
            original_total=order_total,
            discounted_total=max(Decimal('0'), working_total),
            total_discount=total_discount,
            applied_discounts=applied_discounts,
            errors=errors
        )

    def record_coupon_usage(
        self,
        coupon_code: str,
        customer_id: str | None = None,
        sale_id: str | None = None
    ) -> bool:
        """
        Record that a coupon was used.

        Call this after a successful sale.

        Returns:
            True if usage was recorded, False if coupon not found
        """
        try:
            coupon = self.Coupon.objects.get(code__iexact=coupon_code.strip())
            coupon.record_usage(customer_id, sale_id)
            return True
        except self.Coupon.DoesNotExist:
            return False
