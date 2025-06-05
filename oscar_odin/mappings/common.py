"""Common code between mappings."""
from typing import Any, Dict, Optional, Type, Iterable
from operator import attrgetter

from django.db.models import QuerySet, Model
from django.db.models.manager import BaseManager

import odin
from odin.exceptions import MappingExecutionError
from odin.fields import NotProvided
from odin.mapping import (
    ImmediateResult,
    MappingBase,
    MappingMeta,
    force_tuple,
    EMPTY_LIST,
)


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


class NonRegisterableMappingMeta(MappingMeta):
    def __new__(mcs, name, bases, attrs):
        attrs["register_mapping"] = attrs.get("register_mapping", False)
        return super().__new__(mcs, name, bases, attrs)


class OscarBaseMapping(MappingBase, metaclass=NonRegisterableMappingMeta):
    register_mapping = False

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

    def _apply_rule(self, mapping_rule):
        from_fields, action, to_fields, to_list, bind, skip_if_none = mapping_rule

        if from_fields is None:
            from_values = EMPTY_LIST
        else:
            # THIS IS THE ONLY CODE CHANGED COMPARED TO THE ORIGINAL METHOD.
            # IT REPLACES GETATTR WITH ATTRGETTER TO ALLOW NESTED FIELD ACCESS (eg; from_field=("shipping_address.line4"))
            # IT ALSO RETURNS NONE FOR ONE TO ONE FIELDS THAT RAISE RelatedObjectDoesNotExist ERRORS
            from_values = []
            for f in from_fields:
                try:
                    from_values.append(attrgetter(f)(self.source))
                except Exception as e:  # pylint: disable=broad-exception-caught
                    if "RelatedObjectDoesNotExist" in str(type(e)):
                        from_values.append(None)
                    else:
                        raise
            from_values = tuple(from_values)

        if action is None:
            to_values = from_values
        else:
            if isinstance(action, str):
                action = getattr(self, action)

            try:
                if bind:
                    to_values = action(self, *from_values)
                else:
                    to_values = action(*from_values)
            except TypeError as ex:
                raise MappingExecutionError(
                    f"{ex} applying rule {mapping_rule}"
                ) from ex

        if to_list:
            if isinstance(to_values, Iterable):
                to_values = (list(to_values),)
            else:
                to_values = (to_values,)
        else:
            to_values = force_tuple(to_values)

        if len(to_fields) != len(to_values):
            raise MappingExecutionError(
                f"Rule expects {len(to_fields)} fields ({len(to_values)} returned) "
                f"applying rule {mapping_rule}. The `to_list` option might need to be specified"
            )

        if skip_if_none:
            result = {
                f: to_values[i]
                for i, f in enumerate(to_fields)
                if to_values[i] is not None
            }
        else:
            result = {f: to_values[i] for i, f in enumerate(to_fields)}

        if self.ignore_not_provided:
            return {k: v for k, v in result.items() if v is not NotProvided}
        else:
            return result
