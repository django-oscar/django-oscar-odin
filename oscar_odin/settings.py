from importlib import import_module

from django.conf import settings

PREFETCH_PRODUCT_QUERYSET_MODULE = getattr(
    settings,
    "PREFETCH_PRODUCT_QUERYSET_MODULE",
    "oscar_odin.mappings.prefetch.prefetch_product_queryset",
)


def get_prefetch_product_queryset():
    module_path, name = PREFETCH_PRODUCT_QUERYSET_MODULE.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, name)
