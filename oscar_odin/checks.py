from django import VERSION
from django.core.checks import Error, register, Tags
from django.conf import settings


# pylint: disable=unused-argument
@register(Tags.compatibility)
def odin_startup_check(app_configs, **kwargs):
    errors = []

    django_major_version = VERSION[0]

    if django_major_version < 4:
        for _, database in settings.DATABASES.items():
            if database["ENGINE"] == "django.db.backends.sqlite3":
                errors.append(
                    Error(
                        "django-oscar-odin does not support sqlite3 with Django < 4. Please use engines that have can_return_rows_from_bulk_insert set to True (like Postgres) or upgrade your Django version to 4 or higher.",
                        id="django-oscar-odin.E001",
                    )
                )

    return errors
