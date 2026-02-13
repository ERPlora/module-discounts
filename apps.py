from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DiscountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'discounts'
    label = 'discounts'
    verbose_name = _('Discounts')

    def ready(self):
        pass
