"""Extended model mapper for Django models."""
from typing import Sequence

from django.db.models.fields.related import ForeignKey

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
        mapping_type.foreign_key_fields = foreign_key_fields = []

        meta = getmeta(mapping_type.to_obj)

        for relation in meta.related_objects:
            if relation.many_to_many:
                many_to_many_fields.append(
                    (relation.related_name, relation.field.attname)
                )
            elif relation.many_to_one:
                many_to_one_fields.append(
                    (relation.related_name, relation.field.attname)
                )
            elif relation.one_to_many:
                many_to_many_fields.append(
                    (relation.related_name, relation.field.attname)
                )

        for field in meta.fields:
            if isinstance(field, ForeignKey):
                foreign_key_fields.append((field.attname, field.attname))

        return mapping_type


class ModelMapping(MappingBase, metaclass=ModelMappingMeta):
    """Definition of a mapping between two Objects."""

    exclude_fields = []
    mappings = []
    one_to_one_fields: Sequence[str] = []
    many_to_one_fields: Sequence[str] = []
    many_to_many_fields: Sequence[str] = []
    foreign_key_fields: Sequence[str] = []

    def create_object(self, **field_values):
        """Create a new product model."""

        self.context["one_to_one_items"] = one_to_one_items = [
            (name, table_name, field_values.pop(name))
            for name, table_name in self.one_to_one_fields
            if name in field_values
        ]
        self.context["many_to_one_items"] = many_to_one_items = [
            (name, table_name, field_values.pop(name))
            for name, table_name in self.many_to_one_fields
            if name in field_values
        ]
        self.context["many_to_many_items"] = many_to_many_items = [
            (name, table_name, field_values.pop(name))
            for name, table_name in self.many_to_many_fields
            if name in field_values
        ]
        self.context["foreign_key_items"] = foreign_key_items = [
            (name, table_name, field_values.pop(name))
            for name, table_name in self.foreign_key_fields
            if name in field_values
        ]

        return super().create_object(**field_values)
