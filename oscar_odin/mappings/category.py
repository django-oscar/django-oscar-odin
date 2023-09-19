"""Mappings between odin and django-oscar models."""
from decimal import Decimal
from typing import Iterable, List, Optional, Tuple, Type, Union

import odin
from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet
from django.db.models.fields.files import ImageFieldFile
from django.http import HttpRequest
from oscar.apps.partner.strategy import Default as DefaultStrategy
from oscar.core.loading import get_class, get_model

from .. import resources

ProductImageModel = get_model("catalogue", "ProductImage")
CategoryModel = get_model("catalogue", "Category")
ProductClassModel = get_model("catalogue", "ProductClass")
ProductModel = get_model("catalogue", "Product")


def map_queryset(mapping: Type[odin.Mapping], queryset: QuerySet, *, context) -> list:
    """Map a queryset to a resource."""
    return list(mapping.apply(queryset.all(), context=context))


class ProductImageToResource(odin.Mapping):
    """Map from an image model to a resource."""

    from_obj = ProductImageModel
    to_obj = resources.category.Image

    @odin.map_field
    def original(self, value: ImageFieldFile) -> str:
        """Convert value into a pure URL."""
        # Need URL prefix here
        return value.url


class CategoryToResource(odin.Mapping):
    """Map from a category model to a resource."""

    from_obj = CategoryModel
    to_obj = resources.category.Category

    @odin.assign_field
    def meta_title(self) -> str:
        """Map meta title field."""
        return self.source.get_meta_title()

    @odin.map_field
    def image(self, value: ImageFieldFile) -> Optional[str]:
        """Convert value into a pure URL."""
        # Need URL prefix here
        if value:
            return value.url


class ProductClassToResource(odin.Mapping):
    """Map from a product class model to a resource."""

    from_obj = ProductClassModel
    to_obj = resources.category.ProductClass


class ProductToResource(odin.Mapping):
    """Map from a product model to a resource."""

    from_obj = ProductModel
    to_obj = resources.category.Product

    @odin.assign_field
    def title(self) -> str:
        """Map title field."""
        return self.source.get_title()

    @odin.assign_field
    def meta_title(self) -> str:
        """Map meta title field."""
        return self.source.get_meta_title()

    @odin.assign_field
    def images(self) -> List[resources.category.Image]:
        """Map related image."""
        items = self.source.get_all_images()
        return map_queryset(ProductImageToResource, items, context=self.context)

    @odin.assign_field(to_list=True)
    def categories(self):
        """Map related categories."""
        items = self.source.get_categories()
        return map_queryset(CategoryToResource, items, context=self.context)

    @odin.assign_field
    def product_class(self) -> str:
        """Map product class."""
        item = self.source.get_product_class()
        return ProductClassToResource.apply(item, context=self.context)

    @odin.assign_field(to_field=("price", "currency", "availability"))
    def map_stock_price(self) -> Tuple[Decimal, str, int]:
        """Resolve stock price using strategy and decompose into price/currency/availability."""
        strategy: DefaultStrategy = self.context["strategy"]

        # Switch here based on if this is a parent or child product
        price, availability, stock_record = strategy.fetch_for_product(self.source)

        if availability.is_available_to_buy:
            return price.excl_tax, price.currency, availability.num_available
        else:
            # There is no stock record for this product.
            return Decimal(0), "", 0


def product_to_resource(
    product: Union[ProductModel, Iterable[ProductModel]],
    request: Optional[HttpRequest] = None,
    user: Optional[AbstractUser] = None,
    **kwargs
) -> Union[resources.category.Product, Iterable[resources.category.Product]]:
    """Map a product model to a resource.

    This method will except either a single product or an iterable of product
    models (eg a QuerySet), and will return the corresponding resource(s).
    The request and user are optional, but if provided they are supplied to the
    partner strategy selector.

    :param product: A single product model or iterable of product models (eg a QuerySet).
    :param request: The current HTTP request
    :param user: The current user
    :param kwargs: Additional keyword arguments to pass to the strategy selector.
    """
    selector_type = get_class("partner.strategy", "Selector")
    strategy = selector_type().strategy(request=request, user=user, **kwargs)

    return ProductToResource.apply(product, context={"strategy": strategy})
