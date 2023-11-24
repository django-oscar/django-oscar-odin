from typing import Any, Tuple, NamedTuple
from collections import defaultdict

from django.db.models import Model, ManyToManyField, ForeignKey

ForeignRelationResult = Tuple[Model, ManyToManyField, Any]


class RelatedModels(NamedTuple):
    @classmethod
    def from_context(cls, context: dict):
        return cls(
            context["many_to_one_items"] + context["many_to_many_items"],
            context["foreign_key_items"],
        )

    related_items: ForeignRelationResult
    foreign_key_items: Tuple[Model, ForeignKey, Any]


class DatabaseContext(dict):
    many_to_one_items = []
    many_to_many_items = []
    foreign_key_items = []
