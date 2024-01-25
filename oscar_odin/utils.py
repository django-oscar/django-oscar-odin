import contextlib
import time
import math

from django.db import connection, reset_queries

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


def in_bulk(self, instances, field_names):
    """
    Return a dictionary mapping each of the given IDs to the object with
    that ID. If `id_list` isn't provided, evaluate the entire QuerySet.
    """

    max_query_params = connections[self.db].features.max_query_params

    if max_query_params is not None:
        batch_size = math.floor(max_query_params / len(field_names)) - 1
    else:
        batch_size = None

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


def prepare_related_fields_for_save(instance, operation_name, fields):
    """
    This function is taken from models.Model django 4.0,
    It can be used alongside bulk_update for products like:

    for instance in instances_to_update:
        prepare_related_fields_for_save(
            instance, operation_name="bulk_update", fields=fields
        )
    self.Model.objects.bulk_update(instances_to_update, fields=fields)

    This method can be removed when oscar odin drops django 3.2 support.
    """
    fields = [instance._meta.get_field(name) for name in fields]
    if any(not f.concrete or f.many_to_many for f in fields):
        raise ValueError("bulk_update() can only be used with concrete fields.")
    if any(f.primary_key for f in fields):
        raise ValueError("bulk_update() cannot be used with primary key fields.")

    # Ensure that a model instance without a PK hasn't been assigned to
    # a ForeignKey, GenericForeignKey or OneToOneField on this model. If
    # the field is nullable, allowing the save would result in silent data
    # loss.
    for field in instance._meta.concrete_fields:
        if fields and field not in fields:
            continue
        # If the related field isn't cached, then an instance hasn't been
        # assigned and there's no need to worry about this check.
        if field.is_relation and field.is_cached(instance):
            obj = getattr(instance, field.name, None)
            if not obj:
                continue
            # A pk may have been assigned manually to a model instance not
            # saved to the database (or auto-generated in a case like
            # UUIDField), but we allow the save to proceed and rely on the
            # database to raise an IntegrityError if applicable. If
            # constraints aren't supported by the database, there's the
            # unavoidable risk of data corruption.
            if obj.pk is None:
                # Remove the object from a related instance cache.
                if not field.remote_field.multiple:
                    field.remote_field.delete_cached_value(obj)
                raise ValueError(
                    "%s() prohibited to prevent data loss due to unsaved "
                    "related object '%s'." % (operation_name, field.name)
                )
            elif getattr(instance, field.attname) in field.empty_values:
                # Set related object if it has been saved after an
                # assignment.
                setattr(instance, field.name, obj)
            # If the relationship's pk/to_field was changed, clear the
            # cached relationship.
            if getattr(obj, field.target_field.attname) != getattr(
                instance, field.attname
            ):
                field.delete_cached_value(instance)

    # GenericForeignKeys are private.
    for field in instance._meta.private_fields:
        if fields and field not in fields:
            continue
        if (
            field.is_relation
            and field.is_cached(instance)
            and hasattr(field, "fk_field")
        ):
            obj = field.get_cached_value(instance, default=None)
            if obj and obj.pk is None:
                raise ValueError(
                    f"{operation_name}() prohibited to prevent data loss due to "
                    f"unsaved related object '{field.name}'."
                )
