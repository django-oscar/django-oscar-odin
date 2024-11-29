"""Resources for Oscar categories."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from oscar.core.loading import get_model, get_class

import odin
from odin.fields import StringField
from odin.exceptions import ValidationError as OdinValidationError, NON_FIELD_ERRORS

from ..fields import DecimalField

OscarResource = get_class("oscar_odin.resources.base", "OscarResource")

PartnerResource = get_class("oscar_odin.resources.partner", "PartnerResource")
StockRecordResource = get_class("oscar_odin.resources.partner", "StockRecordResource")

ProductModel = get_model("catalogue", "Product")


class OscarCatalogueResource(OscarResource, abstract=True):
    """Base resource for Oscar catalogue application."""

    class Meta:
        allow_field_shadowing = True
        namespace = "oscar.catalogue"


class ProductImageResource(OscarCatalogueResource):
    """An image for a product."""

    class Meta:
        allow_field_shadowing = True
        verbose_name = "Product image"
        verbose_name_plural = "Product images"

    id: Optional[int]
    code: str
    original: Optional[Any]
    caption: Optional[str] = odin.Options(empty=True)
    display_order: int = odin.Options(
        default=0,
        doc_text=(
            "An image with a display order of zero will be the primary"
            " image for a product"
        ),
    )
    date_created: Optional[datetime]

    product: Optional["ProductResource"] = odin.DictAs.delayed(
        lambda: ProductResource, null=True
    )


class CategoryResource(OscarCatalogueResource):
    """A category within Django Oscar."""

    id: Optional[int]
    code: str
    name: Optional[str]
    slug: Optional[str]
    description: Optional[str]
    meta_title: Optional[str]
    meta_description: Optional[str]
    image: Optional[str]
    is_public: Optional[bool]
    ancestors_are_public: Optional[bool]
    depth: Optional[int]
    path: Optional[str]
    children: Optional[List["CategoryResource"]] = odin.ListOf.delayed(
        lambda: CategoryResource
    )


class ProductClassResource(OscarCatalogueResource):
    """A product class within Django Oscar."""

    name: Optional[str]
    slug: str
    requires_shipping: Optional[bool]
    track_stock: Optional[bool]


class ProductAttributeValueResource(OscarCatalogueResource):
    code: str
    value: Any


class ParentProductResource(OscarCatalogueResource):
    upc: str


class ProductRecommentationResource(OscarCatalogueResource):
    upc: str


class ProductResource(OscarCatalogueResource):
    """A product within Django Oscar."""

    id: Optional[int]
    upc: Optional[str]
    structure: str = StringField(choices=ProductModel.STRUCTURE_CHOICES)
    title: str
    slug: Optional[str]
    description: Optional[str] = ""
    meta_title: Optional[str]
    meta_description: Optional[str]
    images: List[ProductImageResource] = odin.Options(empty=True)
    rating: Optional[float]
    is_discountable: bool = True
    is_public: bool = True
    parent: Optional[ParentProductResource]
    priority: int = 0

    # Price information
    price: Decimal = DecimalField(null=True)
    currency: Optional[str] = odin.Options(default=settings.OSCAR_DEFAULT_CURRENCY)
    availability: Optional[int]
    is_available_to_buy: Optional[bool]
    partner: Optional[Any]

    # optionally, you can add a list of stockrecords instead of the above.
    stockrecords: Optional[List[StockRecordResource]] = odin.Options(empty=True)

    product_class: Optional[ProductClassResource] = None
    attributes: Dict[str, Union[Any, None]]
    categories: List[CategoryResource]

    recommended_products: List[ProductRecommentationResource]

    date_created: Optional[datetime]
    date_updated: Optional[datetime]

    children: Optional[List["ProductResource"]] = odin.ListOf.delayed(
        lambda: ProductResource, null=True
    )

    def clean(self):
        if (
            not self.stockrecords
            and (self.price is not None or self.availability is not None)
            and not (
                self.upc is not None
                and self.currency is not None
                and self.partner is not None
            )
        ):
            errors = {
                NON_FIELD_ERRORS: [
                    "upc, currency and partner are required when specifying price or availability"
                ]
            }
            # upc is allready required so we don't need to check for it here
            if (
                self.currency is None
            ):  # currency has a default but it can be set to null by accident
                errors["currency"] = ["Currency can not be empty."]
            if self.partner is None:
                errors["partner"] = ["Partner can not be empty."]

            raise OdinValidationError(errors, code="simpleprice")
