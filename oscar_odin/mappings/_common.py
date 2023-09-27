"""Common code between mappings."""
from typing import Any, Dict, Optional, Type

import odin
from django.db.models import QuerySet
from odin.mapping import ImmediateResult


def map_queryset(
    mapping: Type[odin.Mapping],
    queryset: QuerySet,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> list:
    """Map a queryset to a list of resources.

    This method will call ``QuerySet.all()`` to ensure that the queryset is can
    be directly iterated.

    :param mapping: The mapping type to use.
    :param queryset: The queryset to map.
    :param context: Optional context dictionary to pass to the mapping.
    :return: A list of mapped resources.
    """
    if not issubclass(mapping.from_obj, queryset.model):
        raise ValueError(
            f"Mapping {mapping} cannot map queryset of type {queryset.model}"
        )
    return list(
        mapping.apply(queryset.all(), context=context, mapping_result=ImmediateResult)
    )
