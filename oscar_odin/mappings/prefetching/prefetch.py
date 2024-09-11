from django.db.models import Prefetch

from oscar.core.loading import get_class, get_model

from .registry import prefetch_registry

ProductQuerySet = get_class("catalogue.managers", "ProductQuerySet")

ProductModel = get_model("catalogue", "Product")


def prefetch_product_queryset(
    queryset: ProductQuerySet, include_children: bool = False, **kwargs
) -> ProductQuerySet:
    """
    Optimize the product queryset with registered select_related and prefetch_related operations.

    Args:
        queryset (ProductQuerySet): The initial queryset to optimize.
        include_children (bool): Whether to include prefetches for children.

    Returns:
        ProductQuerySet: The optimized queryset.
    """
    callable_kwargs = {"include_children": include_children, **kwargs}

    select_related_fields = prefetch_registry.get_select_related()
    queryset = queryset.select_related(*select_related_fields)

    prefetches = prefetch_registry.get_prefetches()
    for prefetch in prefetches.values():
        if isinstance(prefetch, (str, Prefetch)):
            queryset = queryset.prefetch_related(prefetch)
        elif callable(prefetch):
            queryset = prefetch(queryset, **callable_kwargs)

    if include_children:
        children_prefetches = prefetch_registry.get_children_prefetches()
        for prefetch in children_prefetches.values():
            if isinstance(prefetch, (str, Prefetch)):
                queryset = queryset.prefetch_related(prefetch)
            elif callable(prefetch):
                queryset = prefetch(queryset, **callable_kwargs)

    return queryset


def register_default_prefetches():
    # ProductToResource.product_class -> get_product_class
    prefetch_registry.register_select_related(["product_class", "parent"])

    # ProductToResource.images -> get_all_images
    prefetch_registry.register_prefetch("images")

    # ProducToResource.map_stock_price -> fetch_for_product
    prefetch_registry.register_prefetch("stockrecords")

    # This gets prefetches somewhere (.categories.all()), it's not in get_categories as that does
    # .browsable() and that's where the prefetch_browsable_categories is for. But if we remove this,
    # the amount of queries will be more again. ToDo: Figure out where this is used and document it.
    prefetch_registry.register_prefetch("categories")

    # The parent and its related fields are prefetched in numerous places in the resource.
    # ProductToResource.product_class -> get_product_class (takes parent product_class if itself has no product_class)
    # ProductToResource.images -> get_all_images (takes parent images if itself has no images)
    prefetch_registry.register_prefetch("parent__product_class")
    prefetch_registry.register_prefetch("parent__images")

    # ProducToResource.attributes -> get_attribute_values
    def prefetch_attribute_values(queryset: ProductQuerySet, **kwargs):
        return queryset.prefetch_attribute_values(
            include_parent_children_attributes=kwargs.get("include_children", False)
        )

    prefetch_registry.register_prefetch(prefetch_attribute_values)

    # ProductToResource.categories -> get_categories
    # ProductToResource.categories -> get_categories -> looks up the parent categories if child
    def prefetch_browsable_categories(queryset: ProductQuerySet, **kwargs):
        return queryset.prefetch_browsable_categories()

    prefetch_registry.register_prefetch(prefetch_browsable_categories)

    # ProductToResource.map_stock_price -> fetch_for_parent -> product.children.public() -> stockrecords
    def prefetch_public_children_stockrecords(queryset: ProductQuerySet, **kwargs):
        return queryset.prefetch_public_children(
            queryset=ProductModel.objects.public().prefetch_related("stockrecords")
        )

    prefetch_registry.register_prefetch(prefetch_public_children_stockrecords)

    # Register children prefetches
    prefetch_registry.register_children_prefetch("children__images")
    prefetch_registry.register_children_prefetch("children__stockrecords")
