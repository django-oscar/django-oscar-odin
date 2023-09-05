DEBUG = True
USE_TZ = True
SITE_ID = 1

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
SECRET_KEY = "123"
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    # "django.contrib.staticfiles",
    # "django.contrib.sites",
    # "django.contrib.flatpages",
    # "oscar.config.Shop",
    # "oscar.apps.catalogue.apps.CatalogueConfig",
]
