from collections import defaultdict
from functools import reduce
from operator import itemgetter, or_
import contextlib
import time
import math

from django.db import connection, connections, reset_queries
from django.db.models import Q
from django.conf import settings

from odin.exceptions import ValidationError
from odin.mapping import MappingResult

from .settings import RESOURCES_TO_DB_CHUNK_SIZE


def get_filters(instances, field_names):
    for ui in instances:
        klaas = {}
        for field_name in field_names:
            field_value = getattr(ui, field_name)
            klaas[field_name] = field_value

        yield Q(**klaas)


def get_query(instances, field_names):
    filters = list((get_filters(instances, field_names)))

    query = filters.pop()
    for query_filter in filters:
        query = query | query_filter

    return query


def in_bulk(self, instances, field_names):
    """
    Return a dictionary mapping each of the given IDs to the object with
    that ID. If `id_list` isn't provided, evaluate the entire QuerySet.
    """

    max_query_params = connections[self.db].features.max_query_params

    if max_query_params is not None:
        batch_size = math.floor(max_query_params / len(field_names)) - 1
    else:
        batch_size = getattr(settings, "ODIN_BATCH_SIZE", 500)

    if batch_size and batch_size < len(instances):
        qs = ()
        for offset in range(0, len(instances), batch_size):
            batch = instances[offset : offset + batch_size]
            query = get_query(batch, field_names)
            qs += tuple(self.filter(query).order_by().values("pk", *field_names))
    else:
        query = get_query(instances, field_names)
        qs = self.filter(query).order_by().values("pk", *field_names)

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


class ErrorLog(list):
    def __init__(self, identifiers=None):
        self.identifiers = identifiers

    def add_error(self, error, record):
        if self.identifiers is not None:
            # Add details to identify the instance that produced this error
            error.identifier_values = [
                str(getattr(record, identifier, "")) for identifier in self.identifiers
            ]
        self.append(error)


def validate_resources(resources, error_identifiers=None):
    errors = ErrorLog(identifiers=error_identifiers)
    valid_resources = []
    if not resources:
        return [], []
    if not isinstance(resources, (list, tuple)):
        if isinstance(resources, MappingResult):
            resources = resources.items
        else:
            resources = [resources]
    for resource in resources:
        try:
            resource.full_clean()
            valid_resources.append(resource)
        except ValidationError as error:
            errors.add_error(error, resource)
    return valid_resources, errors


def chunked(iterable, size=RESOURCES_TO_DB_CHUNK_SIZE, startindex=0):
    """
    Divide an interable into chunks of ``size``

    >>> list(chunked("hahahaha", 2))
    ['ha', 'ha', 'ha', 'ha']
    >>> list(chunked([1,2,3,4,5,6,7], 3))
    [[1, 2, 3], [4, 5, 6], [7]]
    """
    while True:
        chunk = iterable[startindex : startindex + size]
        chunklen = len(chunk)
        if chunklen:
            yield chunk
        if chunklen < size:
            break
        startindex += size


def get_mapped_fields(mapping, *from_field_names):
    keyed_mapping = defaultdict(set)
    exclude_fields = getattr(mapping, "exclude_fields", set())
    # pylint: disable=protected-access
    for mapping_rule in mapping._mapping_rules:
        if mapping_rule.from_field:
            for field_name in mapping_rule.from_field:
                if field_name not in exclude_fields:
                    keyed_mapping[field_name] |= set(mapping_rule.to_field)
        else:
            keyed_mapping[None] |= set(mapping_rule.to_field)

    if from_field_names:
        return reduce(or_, itemgetter(*from_field_names)(keyed_mapping))

    return reduce(or_, keyed_mapping.values())
