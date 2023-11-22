"""Mappings between odin and django-oscar models."""
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import odin
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import QuerySet
from django.db.models.fields.files import ImageFieldFile
from django.http import HttpRequest
from oscar.apps.partner.strategy import Default as DefaultStrategy
from oscar.core.loading import get_class, get_model

from datetime import datetime

from .. import resources
from ..resources.catalogue import Structure
from ._common import map_queryset
from ._model_mapper import ModelMapping

__all__ = (
    "ProductImageToResource",
    "CategoryToResource",
    "ProductClassToResource",
    "ProductToResource",
    "product_to_resource",
    "product_queryset_to_resources",
)


ProductImageModel = get_model("catalogue", "ProductImage")
CategoryModel = get_model("catalogue", "Category")
ProductClassModel = get_model("catalogue", "ProductClass")
ProductModel = get_model("catalogue", "Product")


class ProductImageToResource(odin.Mapping):
    """Map from an image model to a resource."""

    from_obj = ProductImageModel
    to_obj = resources.catalogue.Image

    @odin.map_field
    def original(self, value: ImageFieldFile) -> str:
        """Convert value into a pure URL."""
        # Need URL prefix here
        return value.url


class ProductImageToModel(odin.Mapping):
    """Map from an image resource to a model."""

    from_obj = resources.catalogue.Image
    to_obj = ProductImageModel

    @odin.map_field
    def original(self, value: str) -> str:
        """Convert value into a pure URL."""
        # TODO convert into a form that can be accepted by a model
        return value

    @odin.map_field
    def date_created(self, value: datetime) -> datetime:
        if value:
            return value

        return datetime.now()


class CategoryToResource(odin.Mapping):
    """Map from a category model to a resource."""

    from_obj = CategoryModel
    to_obj = resources.catalogue.Category

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


class CategoryToModel(odin.Mapping):
    """Map from a category resource to a model."""

    from_obj = resources.catalogue.Category
    to_obj = CategoryModel

    @odin.map_field
    def image(self, value: Optional[str]) -> Optional[str]:
        """Convert value into a pure URL."""
        # TODO convert into a form that can be accepted by a model
        return value


class ProductClassToResource(odin.Mapping):
    """Map from a product class model to a resource."""

    from_obj = ProductClassModel
    to_obj = resources.catalogue.ProductClass


class ProductClassToModel(odin.Mapping):
    """Map from a product class resource to a model."""

    from_obj = resources.catalogue.ProductClass
    to_obj = ProductClassModel


class ProductToResource(odin.Mapping):
    """Map from a product model to a resource."""

    from_obj = ProductModel
    to_obj = resources.catalogue.Product

    @odin.map_field
    def structure(self, value: str) -> Structure:
        """Map structure to enum."""
        return Structure(value)

    @odin.assign_field
    def title(self) -> str:
        """Map title field."""
        return self.source.get_title()

    @odin.assign_field
    def meta_title(self) -> str:
        """Map meta title field."""
        return self.source.get_meta_title()

    @odin.assign_field(to_list=True)
    def images(self) -> List[resources.catalogue.Image]:
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

    @staticmethod
    def _attribute_value_to_native_type(item):
        """Handle ProductAttributeValue to native type conversion."""
        obj_type = item.attribute.type
        if obj_type == item.attribute.OPTION:
            return item.value.option

        elif obj_type == item.attribute.MULTI_OPTION:
            return item.value.values_list("option", flat=True)

        elif obj_type == item.attribute.FILE:
            return item.value.url

        elif obj_type == item.attribute.IMAGE:
            return item.value.url

        elif obj_type == item.attribute.ENTITY:
            if hasattr(item.value, "json"):
                return item.value.json()
            else:
                return f"{repr(item.value)} has no json method, can not convert to json"

        # return the value as stored on ProductAttributeValue in the correct type
        return item.value

    @odin.assign_field
    def attributes(self) -> Dict[str, Any]:
        """Map attributes."""
        attribute_value_to_native_type = self._attribute_value_to_native_type
        return {
            item.attribute.code: attribute_value_to_native_type(item)
            for item in self.source.get_attribute_values()
        }

    @odin.assign_field
    def children(self) -> Tuple[Optional[List[resources.catalogue.Product]]]:
        """Children of parent products."""

        if self.context.get("include_children", False) and self.source.is_parent:
            # Return a tuple as an optional list causes problems.
            return (
                map_queryset(
                    ProductToResource, self.source.children, context=self.context
                ),
            )
        return (None,)

    @odin.assign_field(to_field=("price", "currency", "availability"))
    def map_stock_price(self) -> Tuple[Decimal, str, int]:
        """Resolve stock price using strategy and decompose into price/currency/availability."""
        stock_strategy: DefaultStrategy = self.context["stock_strategy"]

        # Switch here based on if this is a parent or child product
        price, availability, stock_record = stock_strategy.fetch_for_product(
            self.source
        )

        if availability.is_available_to_buy:
            return price.excl_tax, price.currency, availability.num_available
        else:
            # There is no stock record for this product.
            return Decimal(0), "", 0


class ProductToModel(ModelMapping):
    """Map from a product resource to a model."""

    from_obj = resources.catalogue.Product
    to_obj = ProductModel

    @odin.map_list_field
    def images(self, values) -> List[ProductImageModel]:
        """Map related image. We save these later in bulk"""
        return ProductImageToModel.apply(values)

    @odin.map_list_field
    def children(self, values) -> List[ProductModel]:
        """Map related image."""
        return []

    @odin.map_field(from_field="product_class", to_field="product_class_id")
    def product_class_id(self, value) -> ProductClassModel:
        return ProductClassToModel.apply(value)

    # @odin.assign_field
    # def categories(self) -> List[CategoryModel]:
    #     """Map related categories."""
    #     return list(CategoryToModel.apply(self.source.categories, context=self.context))


def product_to_resource_with_strategy(
    product: Union[ProductModel, Iterable[ProductModel]],
    stock_strategy: DefaultStrategy,
    include_children: bool = False,
):
    """Map a product model to a resource.

    This method will except either a single product or an iterable of product
    models (eg a QuerySet), and will return the corresponding resource(s).
    The request and user are optional, but if provided they are supplied to the
    partner strategy selector.

    :param product: A single product model or iterable of product models (eg a QuerySet).
    :param stock_strategy: The current HTTP request
    :param include_children: Include children of parent products.
    """
    return ProductToResource.apply(
        product,
        context={
            "stock_strategy": stock_strategy,
            "include_children": include_children,
        },
    )


def product_to_resource(
    product: Union[ProductModel, Iterable[ProductModel]],
    request: Optional[HttpRequest] = None,
    user: Optional[AbstractUser] = None,
    include_children: bool = False,
    **kwargs,
) -> Union[resources.catalogue.Product, Iterable[resources.catalogue.Product]]:
    """Map a product model to a resource.

    This method will except either a single product or an iterable of product
    models (eg a QuerySet), and will return the corresponding resource(s).
    The request and user are optional, but if provided they are supplied to the
    partner strategy selector.

    :param product: A single product model or iterable of product models (eg a QuerySet).
    :param request: The current HTTP request
    :param user: The current user
    :param include_children: Include children of parent products.
    :param kwargs: Additional keyword arguments to pass to the strategy selector.
    """
    selector_type = get_class("partner.strategy", "Selector")
    stock_strategy = selector_type().strategy(request=request, user=user, **kwargs)

    return product_to_resource_with_strategy(product, stock_strategy, include_children)


def product_queryset_to_resources(
    queryset: QuerySet,
    request: Optional[HttpRequest] = None,
    user: Optional[AbstractUser] = None,
    include_children: bool = False,
    **kwargs,
) -> Iterable[resources.catalogue.Product]:
    """Map a queryset of product models to a list of resources.

    The request and user are optional, but if provided they are supplied to the
    partner strategy selector.

    :param queryset: A queryset of product models.
    :param request: The current HTTP request
    :param user: The current user
    :param include_children: Include children of parent products.
    :param kwargs: Additional keyword arguments to pass to the strategy selector.
    """

    query_set = queryset.prefetch_related(
        "images", "product_class", "product_class__options"
    )

    return product_to_resource(
        query_set, request, user, include_children=include_children, **kwargs
    )


def product_to_model(
    product: resources.catalogue.Product,
) -> ProductModel:
    """Map a product resource to a model."""
    context = {}
    
    obj = ProductToModel.apply(product, context=context)

    return obj, context


def product_to_db(
    product: resources.catalogue.Product,
) -> ProductModel:
    """Map a product resource to a model and store in the database.

    The method will handle the nested database saves required to store the entire resource
    within a single transaction.
    """
    obj, context = product_to_model(product)

    with transaction.atomic():
        for fk_name, fk_attname, fk_instance in context.get("foreign_key_items", []):
            fk_instance.save()
            setattr(obj, fk_name, fk_instance.pk)

        obj.save()

        for mtm_name, mtm_attname, instances in context.get("many_to_many_items", []):
            for mtm_instance in instances:
                setattr(mtm_instance, mtm_attname, obj.pk)
                mtm_instance.save()

    return obj
