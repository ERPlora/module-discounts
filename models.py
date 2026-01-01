"""
Models for Discounts module.

Supports:
- Coupons (single-use or multi-use codes)
- Promotions (time-based discounts)
- Product-specific discounts
- Category-based discounts
"""

import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class DiscountType(models.TextChoices):
    """Types of discounts."""
    PERCENTAGE = 'percentage', 'Percentage'
    FIXED_AMOUNT = 'fixed', 'Fixed Amount'
    BUY_X_GET_Y = 'bogo', 'Buy X Get Y'


class DiscountScope(models.TextChoices):
    """What the discount applies to."""
    ENTIRE_ORDER = 'order', 'Entire Order'
    SPECIFIC_PRODUCTS = 'products', 'Specific Products'
    SPECIFIC_CATEGORIES = 'categories', 'Specific Categories'
    MINIMUM_PURCHASE = 'minimum', 'Minimum Purchase'


class Coupon(models.Model):
    """
    Coupon codes for discounts.

    Can be single-use or multi-use with optional limits.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Coupon identification
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Discount configuration
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    # Scope
    scope = models.CharField(
        max_length=20,
        choices=DiscountScope.choices,
        default=DiscountScope.ENTIRE_ORDER
    )
    minimum_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum order amount to apply coupon"
    )
    maximum_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum discount amount (for percentage discounts)"
    )

    # Usage limits
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum total uses (null = unlimited)"
    )
    max_uses_per_customer = models.PositiveIntegerField(
        default=1,
        help_text="Maximum uses per customer"
    )
    current_uses = models.PositiveIntegerField(default=0)

    # Validity period
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def is_valid(self) -> bool:
        """Check if coupon is currently valid."""
        now = timezone.now()

        if not self.is_active:
            return False

        if self.valid_from > now:
            return False

        if self.valid_until and self.valid_until < now:
            return False

        if self.max_uses and self.current_uses >= self.max_uses:
            return False

        return True

    @property
    def remaining_uses(self) -> int | None:
        """Get remaining uses, or None if unlimited."""
        if self.max_uses is None:
            return None
        return max(0, self.max_uses - self.current_uses)

    def can_use(self, customer_id: str | None = None, order_total: Decimal = Decimal('0')) -> tuple[bool, str]:
        """
        Check if coupon can be used.

        Returns:
            Tuple of (can_use: bool, reason: str)
        """
        if not self.is_active:
            return False, "Coupon is not active"

        now = timezone.now()
        if self.valid_from > now:
            return False, "Coupon is not yet valid"

        if self.valid_until and self.valid_until < now:
            return False, "Coupon has expired"

        if self.max_uses and self.current_uses >= self.max_uses:
            return False, "Coupon usage limit reached"

        if self.minimum_purchase and order_total < self.minimum_purchase:
            return False, f"Minimum purchase of {self.minimum_purchase} required"

        # Check customer usage limit
        if customer_id and self.max_uses_per_customer:
            customer_uses = CouponUsage.objects.filter(
                coupon=self,
                customer_id=customer_id
            ).count()
            if customer_uses >= self.max_uses_per_customer:
                return False, "You have already used this coupon"

        return True, "Coupon is valid"

    def calculate_discount(self, order_total: Decimal) -> Decimal:
        """Calculate discount amount for given order total."""
        if self.discount_type == DiscountType.PERCENTAGE:
            discount = order_total * (self.discount_value / 100)
            if self.maximum_discount:
                discount = min(discount, self.maximum_discount)
            return discount
        elif self.discount_type == DiscountType.FIXED_AMOUNT:
            return min(self.discount_value, order_total)
        return Decimal('0')

    def record_usage(self, customer_id: str | None = None, sale_id: str | None = None) -> 'CouponUsage':
        """Record a coupon usage."""
        self.current_uses += 1
        self.save(update_fields=['current_uses', 'updated_at'])

        return CouponUsage.objects.create(
            coupon=self,
            customer_id=customer_id,
            sale_id=sale_id
        )


class CouponUsage(models.Model):
    """Track coupon usage history."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    customer_id = models.CharField(max_length=50, null=True, blank=True)
    sale_id = models.CharField(max_length=50, null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['coupon', 'customer_id']),
        ]


class CouponProduct(models.Model):
    """Products that a coupon applies to (when scope is SPECIFIC_PRODUCTS)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='products')
    product_id = models.CharField(max_length=50)

    class Meta:
        unique_together = ['coupon', 'product_id']


class CouponCategory(models.Model):
    """Categories that a coupon applies to (when scope is SPECIFIC_CATEGORIES)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='categories')
    category_id = models.CharField(max_length=50)

    class Meta:
        unique_together = ['coupon', 'category_id']


class Promotion(models.Model):
    """
    Time-based promotions that apply automatically.

    Unlike coupons, promotions don't require a code.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Promotion identification
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Discount configuration
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    # Scope
    scope = models.CharField(
        max_length=20,
        choices=DiscountScope.choices,
        default=DiscountScope.ENTIRE_ORDER
    )
    minimum_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    maximum_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Validity period
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    # Scheduling
    days_of_week = models.CharField(
        max_length=20,
        blank=True,
        help_text="Comma-separated days (0=Monday, 6=Sunday). Empty = all days"
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Daily start time (null = 00:00)"
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Daily end time (null = 23:59)"
    )

    # Priority (higher = applied first)
    priority = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100)]
    )

    # Stacking
    stackable = models.BooleanField(
        default=False,
        help_text="Can this promotion stack with others?"
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return self.name

    @property
    def is_valid(self) -> bool:
        """Check if promotion is currently valid."""
        now = timezone.now()

        if not self.is_active:
            return False

        if self.valid_from > now or self.valid_until < now:
            return False

        # Check day of week
        if self.days_of_week:
            current_day = str(now.weekday())
            allowed_days = self.days_of_week.split(',')
            if current_day not in allowed_days:
                return False

        # Check time of day
        current_time = now.time()
        if self.start_time and current_time < self.start_time:
            return False
        if self.end_time and current_time > self.end_time:
            return False

        return True

    def calculate_discount(self, order_total: Decimal) -> Decimal:
        """Calculate discount amount for given order total."""
        if self.minimum_purchase and order_total < self.minimum_purchase:
            return Decimal('0')

        if self.discount_type == DiscountType.PERCENTAGE:
            discount = order_total * (self.discount_value / 100)
            if self.maximum_discount:
                discount = min(discount, self.maximum_discount)
            return discount
        elif self.discount_type == DiscountType.FIXED_AMOUNT:
            return min(self.discount_value, order_total)
        return Decimal('0')


class PromotionProduct(models.Model):
    """Products that a promotion applies to."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='products')
    product_id = models.CharField(max_length=50)

    class Meta:
        unique_together = ['promotion', 'product_id']


class PromotionCategory(models.Model):
    """Categories that a promotion applies to."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='categories')
    category_id = models.CharField(max_length=50)

    class Meta:
        unique_together = ['promotion', 'category_id']
