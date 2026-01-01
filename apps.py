from django.apps import AppConfig


class DiscountsConfig(AppConfig):
    """Django app configuration for Discounts module."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'discounts'
    verbose_name = 'Discounts'

    def ready(self):
        """Module initialization."""
        pass
