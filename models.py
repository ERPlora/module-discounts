from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models.base import HubBaseModel


# ============================================================================
# Coupon (code-based discounts)
# ============================================================================

class Coupon(HubBaseModel):
    DISCOUNT_TYPES = [
        ('percentage', _('Percentage')),
        ('fixed', _('Fixed Amount')),
        ('buy_x_get_y', _('Buy X Get Y')),
    ]
    SCOPE_CHOICES = [
        ('order', _('Entire Order')),
        ('products', _('Specific Products')),
        ('categories', _('Specific Categories')),
    ]

    code = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='order')

    min_purchase = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    max_discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )

    # Usage limits
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    usage_per_customer = models.PositiveIntegerField(default=1)
    usage_count = models.PositiveIntegerField(default=0)

    # Validity
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)

    # Buy X Get Y
    buy_quantity = models.PositiveIntegerField(null=True, blank=True)
    get_quantity = models.PositiveIntegerField(null=True, blank=True)
    get_discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
    )

    # Stacking
    priority = models.PositiveIntegerField(default=0)
    stackable = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'discounts_coupon'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hub_id', 'code']),
            models.Index(fields=['hub_id', 'is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def status(self):
        now = timezone.now()
        if not self.is_active:
            return 'inactive'
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return 'exhausted'
        if self.valid_from > now:
            return 'scheduled'
        if self.valid_until and self.valid_until < now:
            return 'expired'
        return 'active'

    @property
    def is_valid(self):
        return self.status == 'active'

    @property
    def remaining_uses(self):
        if self.usage_limit is None:
            return None
        return max(0, self.usage_limit - self.usage_count)

    def can_use(self, customer=None, order_total=Decimal('0')):
        if not self.is_valid:
            return False, f"Coupon is {self.status}"

        if self.min_purchase and order_total < self.min_purchase:
            return False, f"Minimum purchase of {self.min_purchase} required"

        if customer and self.usage_per_customer:
            customer_uses = DiscountUsage.objects.filter(
                coupon=self, customer=customer, is_deleted=False,
            ).count()
            if customer_uses >= self.usage_per_customer:
                return False, "Usage limit per customer reached"

        return True, "Coupon is valid"

    def calculate_discount(self, order_total):
        if order_total < self.min_purchase:
            return Decimal('0.00')

        if self.discount_type == 'percentage':
            discount = order_total * (self.discount_value / 100)
            if self.max_discount:
                discount = min(discount, self.max_discount)
            return discount
        elif self.discount_type == 'fixed':
            return min(self.discount_value, order_total)
        return Decimal('0.00')

    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=['usage_count', 'updated_at'])


# ============================================================================
# Promotion (auto-applied, time-based discounts)
# ============================================================================

class Promotion(HubBaseModel):
    DISCOUNT_TYPES = [
        ('percentage', _('Percentage')),
        ('fixed', _('Fixed Amount')),
        ('buy_x_get_y', _('Buy X Get Y')),
    ]
    SCOPE_CHOICES = [
        ('order', _('Entire Order')),
        ('products', _('Specific Products')),
        ('categories', _('Specific Categories')),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='order')

    min_purchase = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )
    max_discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )

    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    # Schedule
    days_of_week = models.CharField(
        max_length=20, blank=True,
        help_text=_('Comma-separated days (0=Mon, 6=Sun). Empty = all days'),
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    # Buy X Get Y
    buy_quantity = models.PositiveIntegerField(null=True, blank=True)
    get_quantity = models.PositiveIntegerField(null=True, blank=True)
    get_discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
    )

    # Stacking
    priority = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])
    stackable = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'discounts_promotion'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['hub_id', 'is_active']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]

    def __str__(self):
        return self.name

    @property
    def status(self):
        now = timezone.now()
        if not self.is_active:
            return 'inactive'
        if self.valid_from > now:
            return 'scheduled'
        if self.valid_until < now:
            return 'expired'
        return 'active'

    @property
    def is_valid(self):
        if self.status != 'active':
            return False

        now = timezone.now()
        if self.days_of_week:
            current_day = str(now.weekday())
            if current_day not in self.days_of_week.split(','):
                return False

        current_time = now.time()
        if self.start_time and current_time < self.start_time:
            return False
        if self.end_time and current_time > self.end_time:
            return False

        return True

    def calculate_discount(self, order_total):
        if self.min_purchase and order_total < self.min_purchase:
            return Decimal('0.00')

        if self.discount_type == 'percentage':
            discount = order_total * (self.discount_value / 100)
            if self.max_discount:
                discount = min(discount, self.max_discount)
            return discount
        elif self.discount_type == 'fixed':
            return min(self.discount_value, order_total)
        return Decimal('0.00')


# ============================================================================
# Scope models (product/category targeting)
# ============================================================================

class CouponProduct(HubBaseModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='product_scope')
    product = models.ForeignKey(
        'inventory.Product', on_delete=models.CASCADE, related_name='+',
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'discounts_coupon_product'
        unique_together = [('coupon', 'product')]


class CouponCategory(HubBaseModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='category_scope')
    category = models.ForeignKey(
        'inventory.Category', on_delete=models.CASCADE, related_name='+',
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'discounts_coupon_category'
        unique_together = [('coupon', 'category')]


class PromotionProduct(HubBaseModel):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='product_scope')
    product = models.ForeignKey(
        'inventory.Product', on_delete=models.CASCADE, related_name='+',
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'discounts_promotion_product'
        unique_together = [('promotion', 'product')]


class PromotionCategory(HubBaseModel):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='category_scope')
    category = models.ForeignKey(
        'inventory.Category', on_delete=models.CASCADE, related_name='+',
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'discounts_promotion_category'
        unique_together = [('promotion', 'category')]


# ============================================================================
# Conditions (flexible conditions for coupons/promotions)
# ============================================================================

class DiscountCondition(HubBaseModel):
    CONDITION_TYPES = [
        ('min_quantity', _('Minimum Quantity')),
        ('min_amount', _('Minimum Amount')),
        ('customer_group', _('Customer Group')),
        ('first_purchase', _('First Purchase Only')),
        ('day_of_week', _('Day of Week')),
        ('time_of_day', _('Time of Day')),
    ]

    coupon = models.ForeignKey(
        Coupon, on_delete=models.CASCADE, related_name='conditions',
        null=True, blank=True,
    )
    promotion = models.ForeignKey(
        Promotion, on_delete=models.CASCADE, related_name='conditions',
        null=True, blank=True,
    )
    condition_type = models.CharField(max_length=30, choices=CONDITION_TYPES)
    value = models.TextField(help_text=_('Condition value (JSON for complex conditions)'))
    is_inclusive = models.BooleanField(default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'discounts_condition'

    def __str__(self):
        parent = self.coupon or self.promotion
        return f"{parent} - {self.get_condition_type_display()}"


# ============================================================================
# Usage tracking
# ============================================================================

class DiscountUsage(HubBaseModel):
    coupon = models.ForeignKey(
        Coupon, on_delete=models.CASCADE, related_name='usages',
        null=True, blank=True,
    )
    promotion = models.ForeignKey(
        Promotion, on_delete=models.CASCADE, related_name='usages',
        null=True, blank=True,
    )
    sale = models.ForeignKey(
        'sales.Sale', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='discount_usages',
    )
    customer = models.ForeignKey(
        'customers.Customer', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='discount_usages',
    )
    amount_discounted = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
    )
    original_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
    )
    used_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'discounts_usage'
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['used_at']),
        ]

    def __str__(self):
        parent = self.coupon or self.promotion
        return f"{parent} - {self.amount_discounted}"

    @property
    def savings_percentage(self):
        if self.original_amount and self.original_amount > 0:
            return (self.amount_discounted / self.original_amount) * 100
        return Decimal('0.00')
