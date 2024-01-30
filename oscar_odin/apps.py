"""Django App Config for Oscar Odin."""

from django.apps import AppConfig
from django.db.models import Model
from django.utils.translation import gettext_lazy as _
from odin import registration

from .django_resolver import ModelFieldResolver


class OscarOdinAppConfig(AppConfig):
    name = "oscar_odin"
    label = "oscar_odin"
    verbose_name = _("Oscar Odin")

    def ready(self):
        """Hook that Django apps have been loaded."""

        # Register the Django model field resolver
        registration.register_field_resolver(ModelFieldResolver, Model)
