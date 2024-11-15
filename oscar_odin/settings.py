from django.conf import settings

RESOURCES_TO_DB_CHUNK_SIZE = getattr(settings, "RESOURCES_TO_DB_CHUNK_SIZE", 500)
