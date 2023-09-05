#!/usr/bin/env python
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    settings.configure(
        DEBUG=True,
        USE_TZ=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        SECRET_KEY="123",
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            # "django.contrib.staticfiles",
            # "django.contrib.sites",
            # "django.contrib.flatpages",
            # "oscar.config.Shop",
            # "oscar.apps.catalogue.apps.CatalogueConfig",
        ],
        SITE_ID=1,
    )
    # os.environ["DJANGO_SETTINGS_MODULE"] = "tests.test_settings"
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["tests/unit"])
    sys.exit(bool(failures))
