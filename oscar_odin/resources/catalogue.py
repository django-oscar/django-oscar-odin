"""Resources for Oscar categories."""
import enum
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import odin

from ..fields import DecimalField
from ._base import OscarResource


class OscarCatalogue(OscarResource, abstract=True):
    """Base resource for Oscar catalogue application."""

    class Meta:
        namespace = "oscar.catalogue"


class Image(OscarCatalogue):
    """An image for a product."""

    class Meta:
        verbose_name = "Product image"
        verbose_name_plural = "Product images"

    id: int
    original: str  # Image field (URL?)
    caption: str = odin.Options(empty=True)
    display_order: int = odin.Options(
        default=0,
        doc_text=(
            "An image with a display order of zero will be the primary"
            " image for a product"
        ),
    )
    date_created: datetime


class Category(OscarCatalogue):
    """A category within Django Oscar."""

    name: str
    slug: str
    description: str
    meta_title: Optional[str]
    meta_description: Optional[str]
    image: Optional[str]
    is_public: bool
    ancestors_are_public: bool


class ProductClass(OscarCatalogue):
    """A product class within Django Oscar."""

    name: str
    slug: str
    requires_shipping: bool
    track_stock: bool
    options: List[str]


class Structure(str, enum.Enum):
    """Structure of product."""

    STANDALONE = "standalone"
    PARENT = "parent"
    CHILD = "child"


class Product(OscarCatalogue):
    """A product within Django Oscar."""

    id: int
    upc: Optional[str]
    structure: Structure
    title: str
    slug: str
    description: str = odin.Options(empty=True)
    meta_title: Optional[str]
    images: List[Image] = odin.Options(empty=True)
    rating: Optional[float]
    is_discountable: bool

    # Price information
    price: Decimal = DecimalField()
    currency: str
    availability: int

    product_class: ProductClass
    attributes: Dict[str, Any]
    categories: List[Category]
    children: Optional[List["Product"]] = odin.ListOf.delayed(
        lambda: Product, null=True
    )

    date_created: datetime
    date_updated: datetime
