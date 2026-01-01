"""
Unit tests for Discount Service.
"""

import pytest
from decimal import Decimal
from datetime import timedelta

from django.utils import timezone

from discounts.models import Coupon, Promotion, DiscountType, DiscountScope
from discounts.services.discount_service import (
    DiscountService,
    AppliedDiscount,
    DiscountResult,
    get_discount_service
)


# ==============================================================================
# DATACLASS TESTS
# ==============================================================================

class TestAppliedDiscount:
    """Tests for AppliedDiscount dataclass."""

    def test_applied_discount_creation(self):
        """Test creating AppliedDiscount instance."""
        ad = AppliedDiscount(
            source='coupon',
            source_id='123',
            source_name='Test Coupon',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            discount_amount=Decimal('5.00'),
            original_total=Decimal('50.00')
        )
        assert ad.source == 'coupon'
        assert ad.source_id == '123'
        assert ad.source_name == 'Test Coupon'
        assert ad.discount_amount == Decimal('5.00')


class TestDiscountResult:
    """Tests for DiscountResult dataclass."""

    def test_discount_result_creation(self):
        """Test creating DiscountResult instance."""
        result = DiscountResult(
            original_total=Decimal('100.00'),
            discounted_total=Decimal('90.00'),
            total_discount=Decimal('10.00'),
            applied_discounts=[],
            errors=[]
        )
        assert result.original_total == Decimal('100.00')
        assert result.discounted_total == Decimal('90.00')
        assert result.total_discount == Decimal('10.00')

    def test_discount_result_with_discounts(self):
        """Test DiscountResult with applied discounts."""
        discount = AppliedDiscount(
            source='promotion',
            source_id='456',
            source_name='Summer Sale',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            discount_amount=Decimal('20.00'),
            original_total=Decimal('100.00')
        )
        result = DiscountResult(
            original_total=Decimal('100.00'),
            discounted_total=Decimal('80.00'),
            total_discount=Decimal('20.00'),
            applied_discounts=[discount],
            errors=[]
        )
        assert len(result.applied_discounts) == 1
        assert result.applied_discounts[0].source_name == 'Summer Sale'

    def test_discount_result_with_errors(self):
        """Test DiscountResult with errors."""
        result = DiscountResult(
            original_total=Decimal('100.00'),
            discounted_total=Decimal('100.00'),
            total_discount=Decimal('0.00'),
            applied_discounts=[],
            errors=['Invalid coupon code', 'Coupon expired']
        )
        assert len(result.errors) == 2


# ==============================================================================
# SERVICE SINGLETON TESTS
# ==============================================================================

class TestDiscountServiceSingleton:
    """Tests for service singleton."""

    def test_get_discount_service_returns_instance(self):
        """Test get_discount_service returns DiscountService."""
        service = get_discount_service()
        assert isinstance(service, DiscountService)

    def test_get_discount_service_singleton(self):
        """Test get_discount_service returns same instance."""
        service1 = get_discount_service()
        service2 = get_discount_service()
        assert service1 is service2


# ==============================================================================
# SERVICE INITIALIZATION TESTS
# ==============================================================================

class TestDiscountServiceInit:
    """Tests for DiscountService initialization."""

    def test_service_starts_with_no_models_cached(self):
        """Test service starts with no models cached."""
        service = DiscountService()
        assert service._coupon_model is None
        assert service._promotion_model is None


# ==============================================================================
# COUPON VALIDATION TESTS
# ==============================================================================

@pytest.mark.django_db
class TestCouponValidation:
    """Tests for coupon validation."""

    def test_validate_valid_coupon(self, coupon):
        """Test validating a valid coupon."""
        service = DiscountService()
        is_valid, message, result_coupon = service.validate_coupon('TEST10')
        assert is_valid is True
        assert result_coupon == coupon

    def test_validate_nonexistent_coupon(self, db):
        """Test validating nonexistent coupon."""
        service = DiscountService()
        is_valid, message, result_coupon = service.validate_coupon('NOTEXIST')
        assert is_valid is False
        assert result_coupon is None
        assert 'Invalid' in message

    def test_validate_inactive_coupon(self, inactive_coupon):
        """Test validating inactive coupon."""
        service = DiscountService()
        is_valid, message, result_coupon = service.validate_coupon('INACTIVE')
        assert is_valid is False
        assert 'not active' in message

    def test_validate_expired_coupon(self, expired_coupon):
        """Test validating expired coupon."""
        service = DiscountService()
        is_valid, message, result_coupon = service.validate_coupon('EXPIRED')
        assert is_valid is False
        assert 'expired' in message

    def test_validate_coupon_case_insensitive(self, coupon):
        """Test coupon validation is case insensitive."""
        service = DiscountService()
        is_valid, _, _ = service.validate_coupon('test10')
        assert is_valid is True


# ==============================================================================
# APPLY COUPON TESTS
# ==============================================================================

@pytest.mark.django_db
class TestApplyCoupon:
    """Tests for applying coupons."""

    def test_apply_valid_coupon(self, coupon):
        """Test applying valid coupon."""
        service = DiscountService()
        discount, message, result_coupon = service.apply_coupon(
            'TEST10',
            Decimal('100.00')
        )
        assert discount == Decimal('10.00')
        assert result_coupon == coupon

    def test_apply_invalid_coupon(self, db):
        """Test applying invalid coupon."""
        service = DiscountService()
        discount, message, result_coupon = service.apply_coupon(
            'INVALID',
            Decimal('100.00')
        )
        assert discount == Decimal('0')
        assert result_coupon is None


# ==============================================================================
# ACTIVE PROMOTIONS TESTS
# ==============================================================================

@pytest.mark.django_db
class TestActivePromotions:
    """Tests for getting active promotions."""

    def test_get_active_promotions_returns_list(self, promotion):
        """Test get_active_promotions returns list."""
        service = DiscountService()
        promotions = service.get_active_promotions()
        assert isinstance(promotions, list)
        assert len(promotions) >= 1

    def test_get_active_promotions_excludes_inactive(self, db):
        """Test inactive promotions excluded."""
        Promotion.objects.create(
            name='Inactive Sale',
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal('10.00'),
            is_active=False,
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30),
        )
        service = DiscountService()
        promotions = service.get_active_promotions()
        for p in promotions:
            assert p.is_active is True

    def test_get_active_promotions_excludes_expired(self, db):
        """Test expired promotions excluded."""
        Promotion.objects.create(
            name='Expired Sale',
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal('10.00'),
            is_active=True,
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() - timedelta(days=1),
        )
        service = DiscountService()
        promotions = service.get_active_promotions()
        now = timezone.now()
        for p in promotions:
            assert p.valid_until >= now


# ==============================================================================
# APPLICABLE PROMOTIONS TESTS
# ==============================================================================

@pytest.mark.django_db
class TestApplicablePromotions:
    """Tests for getting applicable promotions."""

    def test_get_applicable_promotions_order_scope(self, promotion):
        """Test promotions with order scope are applicable."""
        service = DiscountService()
        applicable = service.get_applicable_promotions(Decimal('100.00'))
        assert promotion in applicable

    def test_get_applicable_promotions_respects_minimum(self, db):
        """Test minimum purchase is respected."""
        promo = Promotion.objects.create(
            name='Min Purchase Sale',
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal('10.00'),
            minimum_purchase=Decimal('50.00'),
            scope=DiscountScope.ENTIRE_ORDER,
            is_active=True,
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30),
        )
        service = DiscountService()

        # Below minimum
        applicable = service.get_applicable_promotions(Decimal('25.00'))
        assert promo not in applicable

        # Above minimum
        applicable = service.get_applicable_promotions(Decimal('75.00'))
        assert promo in applicable


# ==============================================================================
# CALCULATE ORDER DISCOUNTS TESTS
# ==============================================================================

@pytest.mark.django_db
class TestCalculateOrderDiscounts:
    """Tests for calculating order discounts."""

    def test_calculate_with_coupon_only(self, coupon):
        """Test calculation with coupon only."""
        service = DiscountService()
        result = service.calculate_order_discounts(
            order_total=Decimal('100.00'),
            coupon_code='TEST10'
        )
        assert result.original_total == Decimal('100.00')
        assert result.total_discount == Decimal('10.00')
        assert result.discounted_total == Decimal('90.00')
        assert len(result.applied_discounts) == 1
        assert result.applied_discounts[0].source == 'coupon'

    def test_calculate_with_invalid_coupon(self, db):
        """Test calculation with invalid coupon adds error."""
        service = DiscountService()
        result = service.calculate_order_discounts(
            order_total=Decimal('100.00'),
            coupon_code='INVALID'
        )
        assert len(result.errors) == 1
        assert 'Invalid' in result.errors[0]

    def test_calculate_without_coupon_applies_promotions(self, promotion):
        """Test promotions apply when no coupon."""
        service = DiscountService()
        result = service.calculate_order_discounts(
            order_total=Decimal('100.00')
        )
        # Should apply the 20% promotion
        assert result.total_discount >= Decimal('20.00')

    def test_calculate_discounted_total_not_negative(self, db):
        """Test discounted total is never negative."""
        coupon = Coupon.objects.create(
            code='BIG',
            name='Big Discount',
            discount_type=DiscountType.FIXED_AMOUNT,
            discount_value=Decimal('500.00'),
            is_active=True,
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30),
        )
        service = DiscountService()
        result = service.calculate_order_discounts(
            order_total=Decimal('50.00'),
            coupon_code='BIG'
        )
        assert result.discounted_total >= Decimal('0')


# ==============================================================================
# RECORD COUPON USAGE TESTS
# ==============================================================================

@pytest.mark.django_db
class TestRecordCouponUsage:
    """Tests for recording coupon usage."""

    def test_record_usage_valid_coupon(self, coupon):
        """Test recording usage for valid coupon."""
        initial_uses = coupon.current_uses
        service = DiscountService()
        success = service.record_coupon_usage('TEST10', 'cust-123', 'sale-456')
        assert success is True
        coupon.refresh_from_db()
        assert coupon.current_uses == initial_uses + 1

    def test_record_usage_invalid_coupon(self, db):
        """Test recording usage for invalid coupon."""
        service = DiscountService()
        success = service.record_coupon_usage('INVALID')
        assert success is False
