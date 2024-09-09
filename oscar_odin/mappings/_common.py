"""Common code between mappings."""
from typing import Any, Dict, Optional, Type
from django.db.models import QuerySet, Model
from django.db.models.manager import BaseManager

import odin
from odin.mapping import ImmediateResult, MappingBase, MappingMeta


def map_queryset(
    mapping: Type[odin.Mapping],
    queryset: QuerySet,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> list:
    """Map a queryset to a list of resources.

    This method will ensure that the queryset can be directly iterated.

    :param mapping: The mapping type to use.
    :param queryset: The queryset to map.
    :param context: Optional context dictionary to pass to the mapping.
    :return: A list of mapped resources.
    """
    if not issubclass(mapping.from_obj, queryset.model):
        raise ValueError(
            f"Mapping {mapping} cannot map queryset of type {queryset.model}"
        )

    if isinstance(queryset, BaseManager):
        queryset = queryset.all()

    return list(
        mapping.apply(list(queryset), context=context, mapping_result=ImmediateResult)
    )


class OscarBaseMapping(MappingBase, metaclass=MappingMeta):
    def create_object(self, **field_values):
        """
        When subclassing a mapping and resource sometimes the overidden map will somehow result in the values being None
        """
        try:
            new_obj = self.to_obj()  # pylint: disable=E1102

            for key, field_value in field_values.items():
                setattr(new_obj, key, field_value)

            self.pass_model_instance(new_obj)

            return new_obj
        except AttributeError:
            new_obj = super().create_object(**field_value)
            self.pass_model_instance(new_obj)
            return new_obj

    def pass_model_instance(self, obj):
        """
        Passes the model instance (original source) into the extra_attrs method of the resource.
        The resource can then use this to store the model instance as a property for later resources.
        This is useful, as the base resource for each model, isn't saving every model field on the resource.
        Though, later resources that gets mapped from the base resource, might need to access a certain fields
        from the model instance, this way they can access it without doing a separate query, which is good for performance.
        """
        if isinstance(self.source, Model):
            obj.extra_attrs({"model_instance": self.source})
        return obj

    register_mapping = False
