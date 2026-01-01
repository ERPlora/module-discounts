"""
Pytest configuration for Discounts module tests.
"""

import os
import sys
from pathlib import Path

# Ensure Django settings are configured before any imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Add the hub directory to Python path
HUB_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'hub'
if str(HUB_DIR) not in sys.path:
    sys.path.insert(0, str(HUB_DIR))

# Add the modules directory to Python path
MODULES_DIR = Path(__file__).resolve().parent.parent.parent
if str(MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(MODULES_DIR))

# Now setup Django
import django
django.setup()

# Disable debug toolbar during tests to avoid namespace errors
from django.conf import settings
if 'debug_toolbar' in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS = [
        app for app in settings.INSTALLED_APPS if app != 'debug_toolbar'
    ]
if hasattr(settings, 'MIDDLEWARE'):
    settings.MIDDLEWARE = [
        m for m in settings.MIDDLEWARE if 'debug_toolbar' not in m
    ]

# Import pytest and fixtures
import pytest
from decimal import Decimal
from datetime import timedelta
from django.test import Client

from django.utils import timezone

from apps.accounts.models import LocalUser
from apps.configuration.models import StoreConfig


@pytest.fixture
def client():
    """Create test client."""
    return Client()


@pytest.fixture
def local_user(db):
    """Create a test local user."""
    from django.contrib.auth.hashers import make_password
    return LocalUser.objects.create(
        name='Test User',
        email='test@example.com',
        role='admin',
        pin_hash=make_password('1234'),
        is_active=True
    )


@pytest.fixture
def store_config(db):
    """Create store configuration (marks hub as configured)."""
    config = StoreConfig.get_config()
    config.is_configured = True
    config.name = 'Test Store'
    config.save()
    return config


@pytest.fixture
def auth_client(client, local_user, store_config):
    """Create authenticated test client with session."""
    session = client.session
    session['local_user_id'] = str(local_user.id)
    session['user_name'] = local_user.name
    session['user_email'] = local_user.email
    session['user_role'] = local_user.role
    session['store_config_checked'] = True
    session.save()
    return client


@pytest.fixture
def coupon(db):
    """Create a test coupon."""
    from discounts.models import Coupon, DiscountType, DiscountScope

    return Coupon.objects.create(
        code='TEST10',
        name='Test 10% Off',
        description='Test coupon for 10% discount',
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal('10.00'),
        scope=DiscountScope.ENTIRE_ORDER,
        is_active=True,
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def fixed_coupon(db):
    """Create a fixed amount coupon."""
    from discounts.models import Coupon, DiscountType, DiscountScope

    return Coupon.objects.create(
        code='FIXED5',
        name='$5 Off',
        discount_type=DiscountType.FIXED_AMOUNT,
        discount_value=Decimal('5.00'),
        scope=DiscountScope.ENTIRE_ORDER,
        is_active=True,
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def expired_coupon(db):
    """Create an expired coupon."""
    from discounts.models import Coupon, DiscountType, DiscountScope

    return Coupon.objects.create(
        code='EXPIRED',
        name='Expired Coupon',
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal('20.00'),
        scope=DiscountScope.ENTIRE_ORDER,
        is_active=True,
        valid_from=timezone.now() - timedelta(days=30),
        valid_until=timezone.now() - timedelta(days=1),
    )


@pytest.fixture
def inactive_coupon(db):
    """Create an inactive coupon."""
    from discounts.models import Coupon, DiscountType, DiscountScope

    return Coupon.objects.create(
        code='INACTIVE',
        name='Inactive Coupon',
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal('15.00'),
        scope=DiscountScope.ENTIRE_ORDER,
        is_active=False,
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def limited_coupon(db):
    """Create a coupon with usage limits."""
    from discounts.models import Coupon, DiscountType, DiscountScope

    return Coupon.objects.create(
        code='LIMITED',
        name='Limited Use Coupon',
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal('25.00'),
        scope=DiscountScope.ENTIRE_ORDER,
        is_active=True,
        max_uses=10,
        max_uses_per_customer=1,
        current_uses=0,
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def promotion(db):
    """Create a test promotion."""
    from discounts.models import Promotion, DiscountType, DiscountScope

    return Promotion.objects.create(
        name='Summer Sale',
        description='20% off everything',
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal('20.00'),
        scope=DiscountScope.ENTIRE_ORDER,
        is_active=True,
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=30),
        priority=10,
        stackable=False,
    )


@pytest.fixture
def stackable_promotion(db):
    """Create a stackable promotion."""
    from discounts.models import Promotion, DiscountType, DiscountScope

    return Promotion.objects.create(
        name='Extra 5% Off',
        description='Stacks with other promotions',
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal('5.00'),
        scope=DiscountScope.ENTIRE_ORDER,
        is_active=True,
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=30),
        priority=5,
        stackable=True,
    )
