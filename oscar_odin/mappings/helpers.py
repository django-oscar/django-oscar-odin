from typing import Dict, Union, Iterable, Optional, Tuple, List

from django.http import HttpRequest
from django.db.models import QuerySet
from django.contrib.auth.models import AbstractUser

from oscar.core.loading import get_model, get_class, get_classes
from oscar.apps.partner.strategy import Default as DefaultStrategy

from . import constants
from .context import ProductModelMapperContext
from ..settings import RESOURCES_TO_DB_CHUNK_SIZE
from .prefetching.prefetch import prefetch_product_queryset

ProductModel = get_model("catalogue", "Product")

ProductResource = get_class("oscar_odin.resources.catalogue", "ProductResource")
resources_to_db = get_class("oscar_odin.mappings.resources", "resources_to_db")

ProductToResource, ProductToModel = get_classes(
    "oscar_odin.mappings.catalogue", ["ProductToResource", "ProductToModel"]
)
map_queryset, OscarBaseMapping = get_classes(
    "oscar_odin.mappings.common", ["map_queryset", "OscarBaseMapping"]
)


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
) -> Union[ProductResource, Iterable[ProductResource]]:
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
) -> Iterable[ProductResource]:
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


def products_to_db(
    products,
    fields_to_update=constants.ALL_CATALOGUE_FIELDS,
    identifier_mapping=constants.MODEL_IDENTIFIERS_MAPPING,
    product_mapper=ProductToModel,
    delete_related=False,
    clean_instances=True,
    chunk_size=RESOURCES_TO_DB_CHUNK_SIZE,
) -> Tuple[List[ProductModel], Dict]:
    """Map mulitple products to a model and store them in the database.

    The method will first bulk update or create the foreign keys like parent products and productclasses
    After that all the products will be bulk saved.
    At last all related models like images, stockrecords, and related_products can will be saved and set on the product.
    """
    return resources_to_db(
        products,
        fields_to_update,
        identifier_mapping,
        model_mapper=product_mapper,
        context_mapper=ProductModelMapperContext,
        delete_related=delete_related,
        clean_instances=clean_instances,
        chunk_size=chunk_size,
    )
