"""Extended model mapper for Django models."""
from typing import Sequence

from odin.mapping import MappingBase, MappingMeta
from odin.utils import getmeta


class ModelMappingMeta(MappingMeta):
    """Extended type of mapping meta."""

    def __new__(cls, name, bases, attrs):
        mapping_type = super().__new__(cls, name, bases, attrs)

        if mapping_type.to_obj is None:
            return mapping_type

        # Extract out foreign field types.
        mapping_type.one_to_one_fields = one_to_one_fields = []
        mapping_type.many_to_one_fields = many_to_one_fields = []
        mapping_type.many_to_many_fields = many_to_many_fields = []
        related_object = getmeta(mapping_type.to_obj).related_objects
        for relation in related_object:
            if relation.many_to_many:
                one_to_one_fields.append(
                    (relation.related_name, relation.related_model._meta.db_table)
                )
            elif relation.many_to_one:
                many_to_one_fields.append(
                    (relation.related_name, relation.related_model._meta.db_table)
                )
            elif relation.one_to_many:
                many_to_many_fields.append(
                    (relation.related_name, relation.related_model._meta.db_table)
                )

        return mapping_type


class ModelMapping(MappingBase, metaclass=ModelMappingMeta):
    """Definition of a mapping between two Objects."""

    exclude_fields = []
    mappings = []
    one_to_one_fields: Sequence[str] = []
    many_to_one_fields: Sequence[str] = []
    many_to_many_fields: Sequence[str] = []

    def create_object(self, **field_values):
        """Create a new product model."""

        one_to_one_items = [
            (name, table_name, field_values.pop(name))
            for name, table_name in self.one_to_one_fields
            if name in field_values
        ]
        many_to_one_items = [
            (name, table_name, field_values.pop(name))
            for name, table_name in self.many_to_one_fields
            if name in field_values
        ]
        many_to_many_items = [
            (name, table_name, field_values.pop(name))
            for name, table_name in self.many_to_many_fields
            if name in field_values
        ]

        obj = super().create_object(**field_values)

        for name, table_name, value in one_to_one_items:
            if value:
                self.context.setdefault(table_name, []).append(value)
                getattr(obj, name).set(value)

        for name, table_name, value in many_to_one_items:
            if value:
                self.context.setdefault(table_name, []).extend(value)
                getattr(obj, name).sadd(*value)

        for name, table_name, value in many_to_many_items:
            if value:
                self.context.setdefault(table_name, []).extend(value)
                getattr(obj, name).add(*value)

        return obj
