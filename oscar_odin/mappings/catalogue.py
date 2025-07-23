# pylint: disable=W0613
"""Mappings between odin and django-oscar models."""
import odin
import logging

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.db.models.fields.files import ImageFieldFile
from odin.mapping import ImmediateResult
from oscar.apps.partner.strategy import Default as DefaultStrategy
from oscar.core.loading import get_class, get_classes, get_model

from datetime import datetime

from . import constants

logger = logging.getLogger(__name__)

__all__ = (
    "ProductImageToResource",
    "CategoryToResource",
    "ProductClassToResource",
    "ProductToResource",
)


ProductImageModel = get_model("catalogue", "ProductImage")
CategoryModel = get_model("catalogue", "Category")
ProductClassModel = get_model("catalogue", "ProductClass")
ProductModel = get_model("catalogue", "Product")
StockRecordModel = get_model("partner", "StockRecord")

# mappings
ModelMapping = get_class("oscar_odin.mappings.model_mapper", "ModelMapping")
map_queryset, OscarBaseMapping = get_classes(
    "oscar_odin.mappings.common", ["map_queryset", "OscarBaseMapping"]
)
StockRecordToModel = get_class("oscar_odin.mappings.partner", "StockRecordToModel")

# resources
(
    ProductImageResource,
    CategoryResource,
    ProductClassResource,
    ProductResource,
    ParentProductResource,
    ProductRecommentationResource,
) = get_classes(
    "oscar_odin.resources.catalogue",
    [
        "ProductImageResource",
        "CategoryResource",
        "ProductClassResource",
        "ProductResource",
        "ParentProductResource",
        "ProductRecommentationResource",
    ],
)


class ProductImageToResource(OscarBaseMapping):
    """Map from an image model to a resource."""

    from_obj = ProductImageModel
    to_obj = ProductImageResource

    @odin.map_field
    def original(self, value: ImageFieldFile) -> str:
        """Convert value into a pure URL."""
        # Need URL prefix here
        try:
            return value.url
        except ValueError:
            return None


class ProductImageToModel(OscarBaseMapping):
    """Map from an image resource to a model."""

    from_obj = ProductImageResource
    to_obj = ProductImageModel

    @odin.map_field
    def date_created(self, value: datetime) -> datetime:
        if value:
            return value

        return datetime.now()


class CategoryToResource(OscarBaseMapping):
    """Map from a category model to a resource."""

    from_obj = CategoryModel
    to_obj = CategoryResource

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

    from_obj = CategoryResource
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
    to_obj = ProductClassResource


class ProductClassToModel(OscarBaseMapping):
    """Map from a product class resource to a model."""

    from_obj = ProductClassResource
    to_obj = ProductClassModel


class ProductToResource(OscarBaseMapping):
    """Map from a product model to a resource."""

    from_obj = ProductModel
    to_obj = ProductResource

    @odin.assign_field
    def title(self) -> str:
        """Map title field."""
        return self.source.get_title()

    @odin.assign_field
    def meta_title(self) -> str:
        """Map meta title field."""
        return self.source.get_meta_title()

    @odin.assign_field(to_list=True)
    def images(self) -> List[ProductImageResource]:
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
                return [value.option for value in item.value]

            elif obj_type == item.attribute.FILE:
                return item.value.url

            elif obj_type == item.attribute.IMAGE:
                return item.value.url

            elif obj_type == item.attribute.ENTITY:
                if hasattr(item.value, "json"):
                    return item.value.json()
                else:
                    logger.error(
                        "%s has no json method, can not convert to json",
                        repr(item.value),
                    )
                    return None

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
    def children(self) -> Tuple[Optional[List[ProductResource]]]:
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
            price_info = stock_strategy.fetch_for_parent(self.source)
        else:
            price_info = stock_strategy.fetch_for_product(self.source)
        return (
            getattr(price_info.price, "incl_tax", Decimal(0)),
            getattr(price_info.price, "currency", ""),
            getattr(price_info.availability, "num_available", 0),
            price_info.availability.is_available_to_buy,
        )


class ProductToModel(ModelMapping):
    """Map from a product resource to a model."""

    from_obj = ProductResource
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
        from_field=[
            "stockrecords",
            "price",
            "availability",
            "currency",
            "upc",
            "partner",
        ]
    )
    def stockrecords(
        self, stockrecords, price, availability, currency, upc, partner
    ) -> List[StockRecordModel]:
        # This means to use explicitly set stockrecords, rather than the price related fields.
        if stockrecords:
            return StockRecordToModel.apply(stockrecords, context=self.context)

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

    IMPACTED_FIELDS = {
        "images": set(constants.ALL_PRODUCTIMAGE_FIELDS),
        "parent": {constants.PRODUCT_PARENT},
        "categories": {constants.CATEGORY_CODE},
        "stockrecords": set(constants.ALL_STOCKRECORD_FIELDS),
        "recommended_products": {constants.PRODUCT_UPC},
        "product_class": {constants.PRODUCTCLASS_SLUG},
        "price": {
            constants.STOCKRECORD_PARTNER,
            constants.STOCKRECORD_PARTNER_SKU,
            constants.STOCKRECORD_PRICE_CURRENCY,
            constants.STOCKRECORD_PRICE,
        },
        "currency": {
            constants.STOCKRECORD_PARTNER,
            constants.STOCKRECORD_PARTNER_SKU,
            constants.STOCKRECORD_PRICE_CURRENCY,
        },
        "availability": {
            constants.STOCKRECORD_PARTNER,
            constants.STOCKRECORD_PARTNER_SKU,
            constants.STOCKRECORD_PRICE_CURRENCY,
            constants.STOCKRECORD_NUM_IN_STOCK,
        },
        "partner": {constants.STOCKRECORD_PARTNER, constants.STOCKRECORD_PARTNER_SKU},
        "attributes": set(),
        "children": set(),
        "structure": {constants.PRODUCT_STRUCTURE},
        "title": {constants.PRODUCT_TITLE},
        "upc": {constants.PRODUCT_UPC},
        "slug": {constants.PRODUCT_SLUG},
        "meta_title": {constants.PRODUCT_META_TITLE},
        "meta_description": {constants.PRODUCT_META_DESCRIPTION},
        "is_public": {constants.PRODUCT_IS_PUBLIC},
        "description": {constants.PRODUCT_DESCRIPTION},
        "is_discountable": {constants.PRODUCT_IS_DISCOUNTABLE},
        "priority": {constants.PRODUCT_PRIORITY},
        "code": {constants.PRODUCT_CODE},
    }

    @classmethod
    def get_fields_impacted_by_mapping(cls, *from_obj_field_names):
        model_field_names = set()
        # remove the excluded fields from consideration and then determine the
        # impacted model field names.
        for field_name in from_obj_field_names:
            if field_name in cls.exclude_fields:
                continue
            # if there is no registration in IMPACTED_FIELDS, we
            # just take the original fieldname
            fields = cls.IMPACTED_FIELDS.get(field_name)
            if fields is not None:
                model_field_names.update(fields)

        return list(model_field_names)


class RecommendedProductToModel(OscarBaseMapping):
    from_obj = ProductRecommentationResource
    to_obj = ProductModel


class ParentToModel(OscarBaseMapping):
    from_obj = ParentProductResource
    to_obj = ProductModel

    @odin.assign_field
    def structure(self):
        return ProductModel.PARENT
