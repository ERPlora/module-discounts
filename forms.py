from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Coupon, Promotion, DiscountCondition


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code', 'name', 'description', 'discount_type', 'discount_value',
            'scope', 'min_purchase', 'max_discount', 'usage_limit',
            'usage_per_customer', 'valid_from', 'valid_until',
            'priority', 'stackable', 'is_active',
            'buy_quantity', 'get_quantity', 'get_discount_percent',
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('SUMMER20'),
            }),
            'name': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('Coupon name'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 2,
            }),
            'discount_type': forms.Select(attrs={'class': 'select'}),
            'discount_value': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0.01',
            }),
            'scope': forms.Select(attrs={'class': 'select'}),
            'min_purchase': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0',
            }),
            'max_discount': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0',
            }),
            'usage_limit': forms.NumberInput(attrs={
                'class': 'input', 'min': '0',
            }),
            'usage_per_customer': forms.NumberInput(attrs={
                'class': 'input', 'min': '1',
            }),
            'valid_from': forms.DateTimeInput(attrs={
                'class': 'input', 'type': 'datetime-local',
            }),
            'valid_until': forms.DateTimeInput(attrs={
                'class': 'input', 'type': 'datetime-local',
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'input', 'min': '0',
            }),
            'stackable': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'buy_quantity': forms.NumberInput(attrs={
                'class': 'input', 'min': '1',
            }),
            'get_quantity': forms.NumberInput(attrs={
                'class': 'input', 'min': '1',
            }),
            'get_discount_percent': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0', 'max': '100',
            }),
        }


class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = [
            'name', 'description', 'discount_type', 'discount_value',
            'scope', 'min_purchase', 'max_discount',
            'valid_from', 'valid_until', 'days_of_week', 'start_time', 'end_time',
            'priority', 'stackable', 'is_active',
            'buy_quantity', 'get_quantity', 'get_discount_percent',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('Promotion name'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 2,
            }),
            'discount_type': forms.Select(attrs={'class': 'select'}),
            'discount_value': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0.01',
            }),
            'scope': forms.Select(attrs={'class': 'select'}),
            'min_purchase': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0',
            }),
            'max_discount': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0',
            }),
            'valid_from': forms.DateTimeInput(attrs={
                'class': 'input', 'type': 'datetime-local',
            }),
            'valid_until': forms.DateTimeInput(attrs={
                'class': 'input', 'type': 'datetime-local',
            }),
            'days_of_week': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('0,1,2,3,4,5,6'),
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'input', 'type': 'time',
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'input', 'type': 'time',
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'input', 'min': '0', 'max': '100',
            }),
            'stackable': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'buy_quantity': forms.NumberInput(attrs={
                'class': 'input', 'min': '1',
            }),
            'get_quantity': forms.NumberInput(attrs={
                'class': 'input', 'min': '1',
            }),
            'get_discount_percent': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0', 'max': '100',
            }),
        }


class DiscountConditionForm(forms.ModelForm):
    class Meta:
        model = DiscountCondition
        fields = ['condition_type', 'value', 'is_inclusive']
        widgets = {
            'condition_type': forms.Select(attrs={'class': 'select'}),
            'value': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('Condition value'),
            }),
            'is_inclusive': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }
