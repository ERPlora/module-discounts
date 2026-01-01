"""
Unit tests for Discounts models.
"""

import pytest
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from discounts.models import (
    Coupon, CouponUsage, CouponProduct, CouponCategory,
    Promotion, PromotionProduct, PromotionCategory,
    DiscountType, DiscountScope
)


# ==============================================================================
# COUPON MODEL TESTS
# ==============================================================================

class TestCouponModel:
    """Tests for Coupon model."""

    def test_coupon_creation(self, coupon):
        """Test basic coupon creation."""
        assert coupon.code == 'TEST10'
        assert coupon.name == 'Test 10% Off'
        assert coupon.discount_type == DiscountType.PERCENTAGE
        assert coupon.discount_value == Decimal('10.00')
        assert coupon.is_active is True

    def test_coupon_str(self, coupon):
        """Test coupon string representation."""
        assert str(coupon) == 'TEST10 - Test 10% Off'

    def test_coupon_is_valid_active(self, coupon):
        """Test is_valid returns True for active valid coupon."""
        assert coupon.is_valid is True

    def test_coupon_is_valid_inactive(self, inactive_coupon):
        """Test is_valid returns False for inactive coupon."""
        assert inactive_coupon.is_valid is False

    def test_coupon_is_valid_expired(self, expired_coupon):
        """Test is_valid returns False for expired coupon."""
        assert expired_coupon.is_valid is False

    def test_coupon_is_valid_not_yet_started(self, db):
        """Test is_valid returns False for coupon not yet started."""
        coupon = Coupon.objects.create(
            code='FUTURE',
            name='Future Coupon',
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal('10.00'),
            valid_from=timezone.now() + timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30),
            is_active=True
        )
        assert coupon.is_valid is False

    def test_coupon_is_valid_max_uses_reached(self, limited_coupon):
        """Test is_valid returns False when max uses reached."""
        limited_coupon.current_uses = limited_coupon.max_uses
        limited_coupon.save()
        assert limited_coupon.is_valid is False

    def test_coupon_remaining_uses_with_limit(self, limited_coupon):
        """Test remaining_uses calculation."""
        limited_coupon.current_uses = 3
        limited_coupon.save()
        assert limited_coupon.remaining_uses == 7

    def test_coupon_remaining_uses_unlimited(self, coupon):
        """Test remaining_uses returns None for unlimited coupon."""
        assert coupon.remaining_uses is None


class TestCouponCanUse:
    """Tests for Coupon.can_use() method."""

    def test_can_use_valid_coupon(self, coupon):
        """Test can_use returns True for valid coupon."""
        can_use, reason = coupon.can_use()
        assert can_use is True
        assert reason == "Coupon is valid"

    def test_can_use_inactive_coupon(self, inactive_coupon):
        """Test can_use returns False for inactive coupon."""
        can_use, reason = inactive_coupon.can_use()
        assert can_use is False
        assert reason == "Coupon is not active"

    def test_can_use_expired_coupon(self, expired_coupon):
        """Test can_use returns False for expired coupon."""
        can_use, reason = expired_coupon.can_use()
        assert can_use is False
        assert reason == "Coupon has expired"

    def test_can_use_minimum_purchase_not_met(self, db):
        """Test can_use fails when minimum purchase not met."""
        coupon = Coupon.objects.create(
            code='MINPURCHASE',
            name='Minimum Purchase',
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal('10.00'),
            minimum_purchase=Decimal('50.00'),
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30),
            is_active=True
        )
        can_use, reason = coupon.can_use(order_total=Decimal('25.00'))
        assert can_use is False
        assert "Minimum purchase" in reason

    def test_can_use_customer_limit_reached(self, limited_coupon):
        """Test can_use fails when customer has reached limit."""
        # Record a usage for this customer
        CouponUsage.objects.create(
            coupon=limited_coupon,
            customer_id='cust-123'
        )
        can_use, reason = limited_coupon.can_use(customer_id='cust-123')
        assert can_use is False
        assert "already used" in reason


class TestCouponCalculateDiscount:
    """Tests for Coupon.calculate_discount() method."""

    def test_calculate_percentage_discount(self, coupon):
        """Test percentage discount calculation."""
        discount = coupon.calculate_discount(Decimal('100.00'))
        assert discount == Decimal('10.00')

    def test_calculate_fixed_discount(self, fixed_coupon):
        """Test fixed amount discount calculation."""
        discount = fixed_coupon.calculate_discount(Decimal('100.00'))
        assert discount == Decimal('5.00')

    def test_calculate_fixed_discount_exceeds_total(self, fixed_coupon):
        """Test fixed discount doesn't exceed order total."""
        discount = fixed_coupon.calculate_discount(Decimal('3.00'))
        assert discount == Decimal('3.00')

    def test_calculate_percentage_with_max(self, db):
        """Test percentage discount with maximum cap."""
        coupon = Coupon.objects.create(
            code='MAXCAP',
            name='Capped Discount',
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal('50.00'),
            maximum_discount=Decimal('10.00'),
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30),
            is_active=True
        )
        discount = coupon.calculate_discount(Decimal('100.00'))
        assert discount == Decimal('10.00')  # Capped at max


class TestCouponRecordUsage:
    """Tests for Coupon.record_usage() method."""

    def test_record_usage_increments_count(self, coupon):
        """Test recording usage increments current_uses."""
        initial_uses = coupon.current_uses
        coupon.record_usage()
        coupon.refresh_from_db()
        assert coupon.current_uses == initial_uses + 1

    def test_record_usage_creates_usage_record(self, coupon):
        """Test recording usage creates CouponUsage record."""
        usage = coupon.record_usage(customer_id='cust-123', sale_id='sale-456')
        assert usage.coupon == coupon
        assert usage.customer_id == 'cust-123'
        assert usage.sale_id == 'sale-456'


# ==============================================================================
# COUPON RELATED MODELS TESTS
# ==============================================================================

class TestCouponUsage:
    """Tests for CouponUsage model."""

    def test_usage_creation(self, coupon):
        """Test creating usage record."""
        usage = CouponUsage.objects.create(
            coupon=coupon,
            customer_id='cust-123',
            sale_id='sale-456'
        )
        assert usage.coupon == coupon
        assert usage.customer_id == 'cust-123'
        assert usage.used_at is not None


class TestCouponProduct:
    """Tests for CouponProduct model."""

    def test_coupon_product_creation(self, coupon):
        """Test adding product to coupon."""
        cp = CouponProduct.objects.create(
            coupon=coupon,
            product_id='prod-123'
        )
        assert cp.coupon == coupon
        assert cp.product_id == 'prod-123'

    def test_coupon_product_unique(self, coupon):
        """Test product can only be added once to coupon."""
        CouponProduct.objects.create(coupon=coupon, product_id='prod-123')
        with pytest.raises(Exception):
            CouponProduct.objects.create(coupon=coupon, product_id='prod-123')


class TestCouponCategory:
    """Tests for CouponCategory model."""

    def test_coupon_category_creation(self, coupon):
        """Test adding category to coupon."""
        cc = CouponCategory.objects.create(
            coupon=coupon,
            category_id='cat-123'
        )
        assert cc.coupon == coupon
        assert cc.category_id == 'cat-123'


# ==============================================================================
# PROMOTION MODEL TESTS
# ==============================================================================

class TestPromotionModel:
    """Tests for Promotion model."""

    def test_promotion_creation(self, promotion):
        """Test basic promotion creation."""
        assert promotion.name == 'Summer Sale'
        assert promotion.discount_type == DiscountType.PERCENTAGE
        assert promotion.discount_value == Decimal('20.00')
        assert promotion.is_active is True
        assert promotion.priority == 10

    def test_promotion_str(self, promotion):
        """Test promotion string representation."""
        assert str(promotion) == 'Summer Sale'

    def test_promotion_is_valid_active(self, promotion):
        """Test is_valid returns True for active promotion."""
        assert promotion.is_valid is True

    def test_promotion_is_valid_inactive(self, db):
        """Test is_valid returns False for inactive promotion."""
        promo = Promotion.objects.create(
            name='Inactive Sale',
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal('15.00'),
            is_active=False,
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30),
        )
        assert promo.is_valid is False

    def test_promotion_is_valid_expired(self, db):
        """Test is_valid returns False for expired promotion."""
        promo = Promotion.objects.create(
            name='Expired Sale',
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal('15.00'),
            is_active=True,
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() - timedelta(days=1),
        )
        assert promo.is_valid is False

    def test_promotion_is_valid_day_of_week(self, db):
        """Test is_valid respects day of week restriction."""
        today = timezone.now()
        wrong_day = str((today.weekday() + 1) % 7)  # Tomorrow's day number

        promo = Promotion.objects.create(
            name='Wrong Day Sale',
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal('15.00'),
            is_active=True,
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30),
            days_of_week=wrong_day,  # Only valid on a different day
        )
        assert promo.is_valid is False


class TestPromotionCalculateDiscount:
    """Tests for Promotion.calculate_discount() method."""

    def test_calculate_percentage_discount(self, promotion):
        """Test percentage discount calculation."""
        discount = promotion.calculate_discount(Decimal('100.00'))
        assert discount == Decimal('20.00')

    def test_calculate_discount_below_minimum(self, db):
        """Test discount is zero below minimum purchase."""
        promo = Promotion.objects.create(
            name='Min Purchase Sale',
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal('10.00'),
            minimum_purchase=Decimal('50.00'),
            is_active=True,
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30),
        )
        discount = promo.calculate_discount(Decimal('25.00'))
        assert discount == Decimal('0')

    def test_calculate_fixed_discount(self, db):
        """Test fixed amount discount calculation."""
        promo = Promotion.objects.create(
            name='Fixed Sale',
            discount_type=DiscountType.FIXED_AMOUNT,
            discount_value=Decimal('10.00'),
            is_active=True,
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30),
        )
        discount = promo.calculate_discount(Decimal('100.00'))
        assert discount == Decimal('10.00')


# ==============================================================================
# PROMOTION RELATED MODELS TESTS
# ==============================================================================

class TestPromotionProduct:
    """Tests for PromotionProduct model."""

    def test_promotion_product_creation(self, promotion):
        """Test adding product to promotion."""
        pp = PromotionProduct.objects.create(
            promotion=promotion,
            product_id='prod-123'
        )
        assert pp.promotion == promotion
        assert pp.product_id == 'prod-123'


class TestPromotionCategory:
    """Tests for PromotionCategory model."""

    def test_promotion_category_creation(self, promotion):
        """Test adding category to promotion."""
        pc = PromotionCategory.objects.create(
            promotion=promotion,
            category_id='cat-123'
        )
        assert pc.promotion == promotion
        assert pc.category_id == 'cat-123'


# ==============================================================================
# ENUM TESTS
# ==============================================================================

class TestDiscountType:
    """Tests for DiscountType choices."""

    def test_discount_type_values(self):
        """Test discount type enum values."""
        assert DiscountType.PERCENTAGE == 'percentage'
        assert DiscountType.FIXED_AMOUNT == 'fixed'
        assert DiscountType.BUY_X_GET_Y == 'bogo'


class TestDiscountScope:
    """Tests for DiscountScope choices."""

    def test_discount_scope_values(self):
        """Test discount scope enum values."""
        assert DiscountScope.ENTIRE_ORDER == 'order'
        assert DiscountScope.SPECIFIC_PRODUCTS == 'products'
        assert DiscountScope.SPECIFIC_CATEGORIES == 'categories'
        assert DiscountScope.MINIMUM_PURCHASE == 'minimum'
