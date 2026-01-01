"""
URL configuration for Discounts module.
"""

from django.urls import path

from . import views

app_name = 'discounts'

urlpatterns = [
    # Coupon management
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/new/', views.coupon_create, name='coupon_create'),
    path('coupons/<uuid:coupon_id>/', views.coupon_detail, name='coupon_detail'),
    path('coupons/<uuid:coupon_id>/edit/', views.coupon_edit, name='coupon_edit'),
    path('coupons/<uuid:coupon_id>/delete/', views.coupon_delete, name='coupon_delete'),
    path('coupons/<uuid:coupon_id>/toggle/', views.coupon_toggle, name='coupon_toggle'),

    # Promotion management
    path('promotions/', views.promotion_list, name='promotion_list'),
    path('promotions/new/', views.promotion_create, name='promotion_create'),
    path('promotions/<uuid:promotion_id>/', views.promotion_detail, name='promotion_detail'),
    path('promotions/<uuid:promotion_id>/edit/', views.promotion_edit, name='promotion_edit'),
    path('promotions/<uuid:promotion_id>/delete/', views.promotion_delete, name='promotion_delete'),
    path('promotions/<uuid:promotion_id>/toggle/', views.promotion_toggle, name='promotion_toggle'),

    # API endpoints
    path('api/validate-coupon/', views.api_validate_coupon, name='api_validate_coupon'),
    path('api/active-promotions/', views.api_active_promotions, name='api_active_promotions'),
    path('api/calculate-discounts/', views.api_calculate_discounts, name='api_calculate_discounts'),
]
