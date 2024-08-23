"""Common code between mappings."""
from typing import Any, Dict, Optional, Type

import odin
from django.db.models import QuerySet
from odin.mapping import ImmediateResult, MappingBase, MappingMeta


def map_queryset(
    mapping: Type[odin.Mapping],
    queryset: QuerySet,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> list:
    """Map a queryset to a list of resources.

    This method will call ``QuerySet.all()`` to ensure that the queryset can
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


class OscarBaseMapping(MappingBase, metaclass=MappingMeta):
    def create_object(self, **field_values):
        """Create an instance of target object, this method can be customised to handle
        custom object initialisation.

        :param field_values: Dictionary of values for creating the target object.
        """
        try:
            new_obj = self.to_obj()  # pylint: disable=E1102

            for key, field_value in field_values.items():
                setattr(new_obj, key, field_value)

            return new_obj
        except AttributeError:
            return super().create_object(**field_value)

    register_mapping = False
