from django.utils.translation import ugettext_lazy as _

from django.apps import AppConfig


class OscarOdinAppConfig(AppConfig):
    name = "oscar_odin"
    label = "oscar_odin"
    verbose_name = _("Oscar Odin")
