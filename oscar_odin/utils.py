from typing import Any, Tuple, NamedTuple
from collections import defaultdict

from django.db.models import Model, ManyToManyField, ForeignKey, Q
from django.db import connections

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


def in_bulk(self, instances=None, field_names=('pk',)):
    """
    Return a dictionary mapping each of the given IDs to the object with
    that ID. If `id_list` isn't provided, evaluate the entire QuerySet.
    """
    if instances is not None:
        if not instances:
            return {}

        # als id_list helemaal geen list is, dan kan je gewoon de standaard in_bulk gebruiken
        

        batch_size = connections[self.db].features.max_query_params / len(field_names)
        # If the database has a limit on the number of query parameters
        # (e.g. SQLite), retrieve objects in batches if necessary.
        # if batch_size and batch_size < len(id_list):
        #     qs = ()
        #     for offset in range(0, len(id_list), batch_size):
        #         batch = id_list[offset:offset + batch_size]
        #         # we hoeven alleen maar de primary ket te hebben
        #         # je moet hier een models.Q(key_1=value_1, key_2=value2) doen and dan | (or)
        #         filters = []
        #         for ui in id_list:
        #             klaas = {}
        #             for idx, field_name in enumerate(field_names):
        #                 klaas[field_name] = ui[idx]
        #
        #             filters.append(Q(**klaas))
        #
        #         query = filters.pop()
        #         for query_filter in filters:
        #             query | query_filter
        #
        #         qs += tuple(self.filter(query).order_by().values("pk"))
        # else:
        #     qs = self.filter(**{filter_key: id_list}).order_by()
        #
            
        filters = []
        for ui in instances:
            klaas = {}
            for field_name in field_names:
                klaas[field_name] = getattr(ui, field_name)
                
            filters.append(Q(**klaas))
        
        query = filters.pop()
        for query_filter in filters:
            query = query | query_filter

        qs = self.filter(query).order_by().values(*("pk",) + field_names)
    else:
        return {}

    object_mapping = {}
    for obj in qs:
        pk = obj.pop("pk")
        object_mapping[tuple(obj.values())] = pk

    return object_mapping
    
