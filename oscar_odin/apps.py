"""Django App Config for Oscar Odin."""

from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig


class OscarOdinAppConfig(OscarConfig):
    name = "oscar_odin"
    label = "oscar_odin"
    verbose_name = _("Oscar Odin")

    def ready(self):
        """Hook that Django apps have been loaded."""

        # Register the default prefetches for the product queryset
        from oscar_odin.mappings.prefetching.prefetch import register_default_prefetches

        register_default_prefetches()
