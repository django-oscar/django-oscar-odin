"""Mappings between odin and django-oscar models."""
from typing import List, Type

import odin
from django.db.models import QuerySet
from django.db.models.fields.files import ImageFieldFile
from oscar.core.loading import get_model

from . import resources

ProductImageModel = get_model("catalogue", "ProductImage")
ProductModel = get_model("catalogue", "Product")


def map_queryset(mapping: Type[odin.Mapping], queryset: QuerySet) -> list:
    """Map a queryset to a resource."""
    return list(mapping.apply(queryset.all()))


class ProductImageToResource(odin.Mapping):
    """Map from an image model to a resource."""

    from_obj = ProductImageModel
    to_obj = resources.category.Image

    @odin.map_field
    def original(self, value: ImageFieldFile) -> str:
        """Convert value into a pure URL."""
        return value.url


class ProductToResource(odin.Mapping):
    """Map from a product model to a resource."""

    from_obj = ProductModel
    to_obj = resources.category.Product

    @odin.assign_field(to_list=True)
    def images(self) -> List[resources.category.Image]:
        """Map related images."""
        return map_queryset(ProductImageToResource, self.source.images)
