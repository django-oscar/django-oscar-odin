# pylint: disable=W0613
"""Mappings between odin and django-oscar models."""
import odin

from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet
from django.db.models.fields.files import ImageFieldFile
from django.http import HttpRequest
from odin.mapping import ImmediateResult
from oscar.apps.partner.strategy import Default as DefaultStrategy
from oscar.core.loading import get_class, get_model

from datetime import datetime

from .. import resources
from ._common import map_queryset, OscarBaseMapping
from ._model_mapper import ModelMapping
from ..utils import validate_resources
from .prefetching.prefetch import prefetch_product_queryset

from .context import ProductModelMapperContext
from .constants import ALL_CATALOGUE_FIELDS, MODEL_IDENTIFIERS_MAPPING

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
StockRecordModel = get_model("partner", "StockRecord")
ProductAttributeValueModel = get_model("catalogue", "ProductAttributeValue")


class ProductImageToResource(OscarBaseMapping):
    """Map from an image model to a resource."""

    from_obj = ProductImageModel
    to_obj = resources.catalogue.Image

    @odin.map_field
    def original(self, value: ImageFieldFile) -> str:
        """Convert value into a pure URL."""
        # Need URL prefix here
        return value.url


class ProductImageToModel(OscarBaseMapping):
    """Map from an image resource to a model."""

    from_obj = resources.catalogue.Image
    to_obj = ProductImageModel

    @odin.map_field
    def date_created(self, value: datetime) -> datetime:
        if value:
            return value

        return datetime.now()


class CategoryToResource(OscarBaseMapping):
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


class CategoryToModel(OscarBaseMapping):
    """Map from a category resource to a model."""

    from_obj = resources.catalogue.Category
    to_obj = CategoryModel

    @odin.map_field
    def image(self, value: Optional[str]) -> Optional[str]:
        """Convert value into a pure URL."""
        return value

    @odin.map_field
    def depth(self, value):
        if value is not None:
            return value

        return 0

    @odin.map_field
    def ancestors_are_public(self, value):
        return True

    @odin.map_field
    def path(self, value):
        if value is not None:
            return value

        return None

    @odin.map_field
    def description(self, value):
        if value is not None:
            return value

        return None


class ProductClassToResource(OscarBaseMapping):
    """Map from a product class model to a resource."""

    from_obj = ProductClassModel
    to_obj = resources.catalogue.ProductClass


class ProductClassToModel(OscarBaseMapping):
    """Map from a product class resource to a model."""

    from_obj = resources.catalogue.ProductClass
    to_obj = ProductClassModel


class ProductToResource(OscarBaseMapping):
    """Map from a product model to a resource."""

    from_obj = ProductModel
    to_obj = resources.catalogue.Product

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
        # Note: categories are prefetched with the 'to_attr' method, this means it's a list and not a queryset.
        return list(
            CategoryToResource.apply(
                items, context=self.context, mapping_result=ImmediateResult
            )
        )

    @odin.assign_field
    def product_class(self) -> str:
        """Map product class."""
        item = self.source.get_product_class()
        return ProductClassToResource.apply(item, context=self.context)

    @staticmethod
    def _attribute_value_to_native_type(item):
        """Handle ProductAttributeValue to native type conversion."""
        try:
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
        except AttributeError:
            return item.value_as_text

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

    @odin.assign_field(
        to_field=("price", "currency", "availability", "is_available_to_buy")
    )
    def map_stock_price(self) -> Tuple[Decimal, str, int, bool]:
        """Resolve stock price using strategy and decompose into price/currency/availability."""
        stock_strategy: DefaultStrategy = self.context["stock_strategy"]

        if self.source.is_parent:
            price, availability, _ = stock_strategy.fetch_for_parent(self.source)
        else:
            price, availability, _ = stock_strategy.fetch_for_product(self.source)
        return (
            getattr(price, "excl_tax", Decimal(0)),
            getattr(price, "currency", ""),
            getattr(availability, "num_available", 0),
            availability.is_available_to_buy,
        )


class ProductToModel(ModelMapping):
    """Map from a product resource to a model."""

    from_obj = resources.catalogue.Product
    to_obj = ProductModel

    mappings = (odin.define(from_field="children", skip_if_none=True),)

    def get_related_field_values(self, field_values):
        attribute_values = field_values.pop("attributes", [])
        context = super().get_related_field_values(field_values)
        context["attribute_values"] = attribute_values
        return context

    def add_related_field_values_to_context(self, parent, related_field_values):
        parent.attr.initialize()
        for key, value in related_field_values["attribute_values"].items():
            parent.attr.set(key, value)

        super().add_related_field_values_to_context(parent, related_field_values)

    @odin.map_list_field
    def images(self, values) -> List[ProductImageModel]:
        """Map related image. We save these later in bulk"""
        return ProductImageToModel.apply(values)

    @odin.map_field
    def parent(self, parent):
        if parent:
            return ParentToModel.apply(parent)

        return None

    @odin.map_list_field
    def categories(self, values) -> List[CategoryModel]:
        return CategoryToModel.apply(values)

    @odin.map_list_field(
        from_field=["price", "availability", "currency", "upc", "partner"]
    )
    def stockrecords(
        self, price, availability, currency, upc, partner
    ) -> List[StockRecordModel]:
        if upc and currency and partner:
            return [
                StockRecordModel(
                    price=price,
                    num_in_stock=availability,
                    price_currency=currency,
                    partner=partner,
                    partner_sku=upc,
                )
            ]

        return []

    @odin.map_list_field
    def recommended_products(self, values):
        if values:
            return RecommendedProductToModel.apply(values)

        return []

    @odin.map_field
    def product_class(self, value) -> ProductClassModel:
        if not value or self.source.structure == ProductModel.CHILD:
            return None

        return ProductClassToModel.apply(value)


class RecommendedProductToModel(OscarBaseMapping):
    from_obj = resources.catalogue.ProductRecommentation
    to_obj = ProductModel


class ParentToModel(OscarBaseMapping):
    from_obj = resources.catalogue.ParentProduct
    to_obj = ProductModel

    @odin.assign_field
    def structure(self):
        return ProductModel.PARENT


def product_to_resource_with_strategy(
    product: Union[ProductModel, Iterable[ProductModel]],
    stock_strategy: DefaultStrategy,
    include_children: bool = False,
    product_mapper: OscarBaseMapping = ProductToResource,
):
    """Map a product model to a resource.

    This method will accept either a single product or an iterable of product
    models (eg a QuerySet), and will return the corresponding resource(s).
    The request and user are optional, but if provided they are supplied to the
    partner strategy selector.

    :param product: A single product model or iterable of product models (eg a QuerySet).
    :param stock_strategy: The current HTTP request
    :param include_children: Include children of parent products.
    """
    return product_mapper.apply(
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
    product_mapper: OscarBaseMapping = ProductToResource,
    **kwargs,
) -> Union[resources.catalogue.Product, Iterable[resources.catalogue.Product]]:
    """Map a product model to a resource.

    This method will accept either a single product or an iterable of product
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
    return product_to_resource_with_strategy(
        product, stock_strategy, include_children, product_mapper=product_mapper
    )


def product_queryset_to_resources(
    queryset: QuerySet,
    request: Optional[HttpRequest] = None,
    user: Optional[AbstractUser] = None,
    include_children: bool = False,
    product_mapper=ProductToResource,
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

    queryset = prefetch_product_queryset(queryset, include_children)

    return product_to_resource(
        queryset,
        request,
        user,
        include_children,
        product_mapper,
        **kwargs,
    )


def products_to_model(
    products: List[resources.catalogue.Product],
    product_mapper=ProductToModel,
    delete_related=False,
) -> Tuple[List[ProductModel], Dict]:
    context = ProductModelMapperContext(ProductModel, delete_related=delete_related)

    result = product_mapper.apply(products, context=context)

    try:
        return (list(result), context)
    except TypeError:  # it is not a list
        return ([result], context)


def products_to_db(
    products,
    fields_to_update=ALL_CATALOGUE_FIELDS,
    identifier_mapping=MODEL_IDENTIFIERS_MAPPING,
    product_mapper=ProductToModel,
    delete_related=False,
    clean_instances=True,
) -> Tuple[List[ProductModel], Dict]:
    """Map mulitple products to a model and store them in the database.

    The method will first bulk update or create the foreign keys like parent products and productclasses
    After that all the products will be bulk saved.
    At last all related models like images, stockrecords, and related_products can will be saved and set on the product.
    """
    _, errors = validate_resources(products)
    if errors:
        return [], errors
    instances, context = products_to_model(
        products,
        product_mapper=product_mapper,
        delete_related=delete_related,
    )

    products, errors = context.bulk_save(
        instances,
        fields_to_update,
        identifier_mapping,
        clean_instances,
    )

    return products, errors
