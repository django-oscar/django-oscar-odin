import contextlib
import time
import math

from django.db import connection, reset_queries

from typing import Any, Tuple, NamedTuple
from collections import defaultdict

from django.db.models import Model, ManyToManyField, ForeignKey, Q
from django.db import connections

def get_filters(instances, field_names):
    for ui in instances:
        klaas = {}
        for field_name in field_names:
            field_value = getattr(ui, field_name)
            klaas[field_name] = field_value

        yield Q(**klaas)


def get_query(instances, field_names):
    filters = list(get_filters(instances, field_names))

    query = filters.pop()
    for query_filter in filters:
        query = query | query_filter
        
    return query


def in_bulk(self, instances=None, field_names=('pk',)):
    """
    Return a dictionary mapping each of the given IDs to the object with
    that ID. If `id_list` isn't provided, evaluate the entire QuerySet.
    """
    if len(field_names) < 1:
        return {}

    if instances is not None:
        if not instances:
            return {}

        batch_size = math.floor(connections[self.db].features.max_query_params / len(field_names)) - 1

        if batch_size and batch_size < len(instances):
            qs = ()
            for offset in range(0, len(instances), batch_size):
                batch = instances[offset:offset + batch_size]
                query = get_query(batch, field_names)
                qs += tuple(self.filter(query).order_by().values(*("pk",) + field_names))
        else:
            query = get_query(instances, field_names)
            qs = self.filter(query).order_by().values(*("pk",) + field_names)
    else:
        return {}

    object_mapping = defaultdict(tuple)
    for obj in qs:
        pk = obj.pop("pk")
        object_mapping[tuple(obj.values())] = pk

    return object_mapping


@contextlib.contextmanager
def querycounter(*labels, print_queries=False):
    reset_queries()
    start = time.time()
    yield
    print(" ".join([str(l) for l in labels]), "--------------" * 6)
    print("time: ", time.time() - start)
    print("num queries", len(connection.queries))
    if print_queries:
        for q in connection.queries:
            print("   ", q)
