"""Extended model mapper for Django models."""
from typing import Sequence, cast

from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.db.models.fields.reverse_related import (
    OneToOneRel,
    ManyToOneRel,
    ManyToManyRel,
)
from django.db.models.options import Options

from odin.mapping import MappingBase, MappingMeta
from odin.utils import getmeta


class ModelMappingMeta(MappingMeta):
    """Extended type of mapping meta."""

    def __new__(cls, name, bases, attrs):
        mapping_type = super().__new__(cls, name, bases, attrs)

        if mapping_type.to_obj is None:
            return mapping_type

        meta = cast(Options, getmeta(mapping_type.to_obj))

        # Extract out foreign field types.
        mapping_type.many_to_one_fields = many_to_one_fields = []
        mapping_type.many_to_many_fields = many_to_many_fields = []
        mapping_type.foreign_key_fields = [
            field for field in meta.fields if isinstance(field, ForeignKey)
        ]

        # Break out related objects by their type
        for relation in meta.related_objects:
            if relation.many_to_many:
                many_to_many_fields.append(relation)
            elif relation.many_to_one:
                many_to_one_fields.append(relation)
            elif relation.one_to_many:
                many_to_one_fields.append(relation)

        return mapping_type


class ModelMapping(MappingBase, metaclass=ModelMappingMeta):
    """Definition of a mapping between two Objects."""

    exclude_fields = []
    mappings = []

    # Specific fields
    many_to_one_fields: Sequence[ManyToOneRel] = []
    many_to_many_fields: Sequence[ManyToManyRel] = []
    foreign_key_fields: Sequence[ForeignKey] = []

    def create_object(self, **field_values):
        """Create a new product model."""
        many_to_one_items = [
            (relation, field_values.pop(relation.related_name))
            for relation in self.many_to_one_fields
            if relation.related_name in field_values
        ]
        many_to_many_items = [
            (relation, field_values.pop(relation.related_name))
            for relation in self.many_to_many_fields
            if relation.related_name in field_values
        ]
        foreign_key_items = [
            (field, field_values.pop(field.name))
            for field in self.foreign_key_fields
            if field.name in field_values
        ]

        parent = super().create_object(**field_values)

        self.context["many_to_one_items"] = [
            (parent, *item) for item in many_to_one_items
        ]
        self.context["many_to_many_items"] = [
            (parent, *item) for item in many_to_many_items
        ]
        self.context["foreign_key_items"] = [
            (parent, *item) for item in foreign_key_items
        ]

        return parent
