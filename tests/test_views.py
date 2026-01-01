"""
Integration tests for Discounts views.

Tests URL routing, API endpoints, and authentication.
"""

import pytest
import json
from decimal import Decimal

from django.urls import resolve

from discounts import views
from discounts.models import Coupon, Promotion


# ==============================================================================
# URL ROUTING TESTS
# ==============================================================================

@pytest.mark.django_db
class TestURLRouting:
    """Tests for URL routing and resolution."""

    def test_coupon_list_url_resolves(self):
        """Test coupon list URL resolves."""
        resolver = resolve('/modules/discounts/coupons/')
        assert resolver.func == views.coupon_list

    def test_coupon_create_url_resolves(self):
        """Test coupon create URL resolves."""
        resolver = resolve('/modules/discounts/coupons/new/')
        assert resolver.func == views.coupon_create

    def test_coupon_detail_url_resolves(self):
        """Test coupon detail URL resolves."""
        resolver = resolve('/modules/discounts/coupons/00000000-0000-0000-0000-000000000001/')
        assert resolver.func == views.coupon_detail

    def test_coupon_edit_url_resolves(self):
        """Test coupon edit URL resolves."""
        resolver = resolve('/modules/discounts/coupons/00000000-0000-0000-0000-000000000001/edit/')
        assert resolver.func == views.coupon_edit

    def test_coupon_delete_url_resolves(self):
        """Test coupon delete URL resolves."""
        resolver = resolve('/modules/discounts/coupons/00000000-0000-0000-0000-000000000001/delete/')
        assert resolver.func == views.coupon_delete

    def test_coupon_toggle_url_resolves(self):
        """Test coupon toggle URL resolves."""
        resolver = resolve('/modules/discounts/coupons/00000000-0000-0000-0000-000000000001/toggle/')
        assert resolver.func == views.coupon_toggle

    def test_promotion_list_url_resolves(self):
        """Test promotion list URL resolves."""
        resolver = resolve('/modules/discounts/promotions/')
        assert resolver.func == views.promotion_list

    def test_promotion_create_url_resolves(self):
        """Test promotion create URL resolves."""
        resolver = resolve('/modules/discounts/promotions/new/')
        assert resolver.func == views.promotion_create

    def test_promotion_detail_url_resolves(self):
        """Test promotion detail URL resolves."""
        resolver = resolve('/modules/discounts/promotions/00000000-0000-0000-0000-000000000001/')
        assert resolver.func == views.promotion_detail

    def test_promotion_edit_url_resolves(self):
        """Test promotion edit URL resolves."""
        resolver = resolve('/modules/discounts/promotions/00000000-0000-0000-0000-000000000001/edit/')
        assert resolver.func == views.promotion_edit

    def test_api_validate_coupon_url_resolves(self):
        """Test API validate coupon URL resolves."""
        resolver = resolve('/modules/discounts/api/validate-coupon/')
        assert resolver.func == views.api_validate_coupon

    def test_api_active_promotions_url_resolves(self):
        """Test API active promotions URL resolves."""
        resolver = resolve('/modules/discounts/api/active-promotions/')
        assert resolver.func == views.api_active_promotions

    def test_api_calculate_discounts_url_resolves(self):
        """Test API calculate discounts URL resolves."""
        resolver = resolve('/modules/discounts/api/calculate-discounts/')
        assert resolver.func == views.api_calculate_discounts


# ==============================================================================
# AUTHENTICATION TESTS
# ==============================================================================

@pytest.mark.django_db
class TestAuthentication:
    """Tests for view authentication requirements."""

    def test_api_validate_coupon_requires_auth(self, client, store_config):
        """Test API validate coupon requires authentication."""
        response = client.get('/modules/discounts/api/validate-coupon/')
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_api_active_promotions_requires_auth(self, client, store_config):
        """Test API active promotions requires authentication."""
        response = client.get('/modules/discounts/api/active-promotions/')
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_coupon_delete_requires_auth(self, client, store_config):
        """Test coupon delete requires authentication."""
        response = client.post('/modules/discounts/coupons/00000000-0000-0000-0000-000000000001/delete/')
        assert response.status_code == 302
        assert '/login/' in response.url


# ==============================================================================
# API ENDPOINT TESTS
# ==============================================================================

@pytest.mark.django_db
class TestAPIEndpoints:
    """Tests for API endpoints."""

    def test_api_validate_coupon_valid(self, auth_client, coupon):
        """Test API validate coupon with valid code."""
        response = auth_client.get(
            '/modules/discounts/api/validate-coupon/',
            {'code': 'TEST10', 'total': '100.00'}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['valid'] is True
        assert 'discount_amount' in data

    def test_api_validate_coupon_invalid(self, auth_client, store_config):
        """Test API validate coupon with invalid code."""
        response = auth_client.get(
            '/modules/discounts/api/validate-coupon/',
            {'code': 'INVALID'}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['valid'] is False

    def test_api_active_promotions(self, auth_client, promotion):
        """Test API active promotions."""
        response = auth_client.get('/modules/discounts/api/active-promotions/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'promotions' in data
        assert isinstance(data['promotions'], list)

    def test_api_calculate_discounts(self, auth_client, coupon):
        """Test API calculate discounts."""
        response = auth_client.post(
            '/modules/discounts/api/calculate-discounts/',
            json.dumps({
                'total': '100.00',
                'coupon_code': 'TEST10'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'original_total' in data
        assert 'discounted_total' in data
        assert 'total_discount' in data

    def test_api_calculate_discounts_invalid_json(self, auth_client, store_config):
        """Test API calculate discounts with invalid JSON."""
        response = auth_client.post(
            '/modules/discounts/api/calculate-discounts/',
            'invalid json',
            content_type='application/json'
        )
        assert response.status_code == 400


# ==============================================================================
# COUPON MANAGEMENT TESTS
# ==============================================================================

@pytest.mark.django_db
class TestCouponManagement:
    """Tests for coupon management endpoints."""

    def test_toggle_coupon_active_to_inactive(self, auth_client, coupon):
        """Test toggling active coupon to inactive."""
        assert coupon.is_active is True
        response = auth_client.post(f'/modules/discounts/coupons/{coupon.id}/toggle/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['is_active'] is False

    def test_toggle_coupon_inactive_to_active(self, auth_client, inactive_coupon):
        """Test toggling inactive coupon to active."""
        assert inactive_coupon.is_active is False
        response = auth_client.post(f'/modules/discounts/coupons/{inactive_coupon.id}/toggle/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['is_active'] is True

    def test_delete_coupon(self, auth_client, coupon):
        """Test deleting a coupon."""
        coupon_id = coupon.id
        response = auth_client.post(f'/modules/discounts/coupons/{coupon_id}/delete/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert not Coupon.objects.filter(id=coupon_id).exists()


# ==============================================================================
# PROMOTION MANAGEMENT TESTS
# ==============================================================================

@pytest.mark.django_db
class TestPromotionManagement:
    """Tests for promotion management endpoints."""

    def test_toggle_promotion(self, auth_client, promotion):
        """Test toggling promotion status."""
        initial_status = promotion.is_active
        response = auth_client.post(f'/modules/discounts/promotions/{promotion.id}/toggle/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['is_active'] != initial_status

    def test_delete_promotion(self, auth_client, promotion):
        """Test deleting a promotion."""
        promotion_id = promotion.id
        response = auth_client.post(f'/modules/discounts/promotions/{promotion_id}/delete/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert not Promotion.objects.filter(id=promotion_id).exists()
