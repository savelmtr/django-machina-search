from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PostgresForumSearchAppConfig(AppConfig):
    label = 'machina_search'
    name = 'machina_search'
    verbose_name = _('Forum searches for Django-Machina')
