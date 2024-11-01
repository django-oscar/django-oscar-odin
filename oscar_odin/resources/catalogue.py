"""Resources for Oscar categories."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from oscar.core.loading import get_model, get_class
import odin
from odin.fields import StringField

from ..fields import DecimalField

OscarResource = get_class("oscar_odin.resources.base", "OscarResource")

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


class ProductClassResource(OscarCatalogueResource):
    """A product class within Django Oscar."""

    name: Optional[str]
    slug: str
    requires_shipping: Optional[bool]
    track_stock: Optional[bool]


class StockRecordResource(OscarCatalogueResource):
    id: Optional[int]
    partner_sku: str
    num_in_stock: Optional[int]
    num_allocated: Optional[int]
    price: Decimal = DecimalField()
    currency: Optional[str]


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
    images: List[ProductImageResource] = odin.Options(empty=True)
    rating: Optional[float]
    is_discountable: bool = True
    is_public: bool = True
    parent: Optional[ParentProductResource]
    priority: int = 0

    # Price information
    price: Decimal = DecimalField(null=True)
    currency: Optional[str]
    availability: Optional[int]
    is_available_to_buy: Optional[bool]
    partner: Optional[Any]

    product_class: Optional[ProductClassResource] = None
    attributes: Dict[str, Union[Any, None]]
    categories: List[CategoryResource]

    recommended_products: List[ProductRecommentationResource]

    date_created: Optional[datetime]
    date_updated: Optional[datetime]

    children: Optional[List["ProductResource"]] = odin.ListOf.delayed(
        lambda: ProductResource, null=True
    )
