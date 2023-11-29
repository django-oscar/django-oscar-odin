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


def in_bulk(self, id_list=None, *, field_names=('pk',)):
    """
    Return a dictionary mapping each of the given IDs to the object with
    that ID. If `id_list` isn't provided, evaluate the entire QuerySet.
    """
    assert not self.query.is_sliced, \
        "Cannot use 'limit' or 'offset' with in_bulk"

    if id_list is not None:
        if not id_list:
            return {}

        # als id_list helemaal geen list is, dan kan je gewoon de standaard in_bulk gebruiken

        filter_key = '{}__in'.format(field_name)
        batch_size = connections[self.db].features.max_query_params
        id_list = tuple(id_list)
        # If the database has a limit on the number of query parameters
        # (e.g. SQLite), retrieve objects in batches if necessary.
        if batch_size and batch_size < len(id_list):
            qs = ()
            for offset in range(0, len(id_list), batch_size):
                batch = id_list[offset:offset + batch_size]
                # we hoeven alleen maar de primary ket te hebben
                # je moet hier een models.Q(key_1=value_1, key_2=value2) doen and dan | (or)
                qs += tuple(self.filter(**{filter_key: batch}).order_by().values("pk"))
        else:
            qs = self.filter(**{filter_key: id_list}).order_by()
    else:
        qs = self._chain()

    return {getattr(obj, field_name): obj for obj in qs}
