from oscar.core.loading import get_class

from ..settings import RESOURCES_TO_DB_CHUNK_SIZE
from ..utils import chunked

ModelMapperContext = get_class("oscar_odin.mappings.context", "ModelMapperContext")
validate_resources = get_class("oscar_odin.utils", "validate_resources")


def resources_to_db(
    resources,
    fields_to_update,
    identifier_mapping,
    model_mapper,
    context_mapper=ModelMapperContext,
    delete_related=False,
    clean_instances=True,
    skip_invalid_resources=False,
    error_identifiers=None,
    chunk_size=RESOURCES_TO_DB_CHUNK_SIZE,
):
    """Map mulitple resources to a model and store them in the database.

    The method will first bulk update or create the foreign keys
    After that all the resources will be bulk saved.
    At last all related models can will be saved and set on the record.
    """
    error_identifiers = error_identifiers or identifier_mapping.get(model_mapper.to_obj)
    valid_resources, resource_errors = validate_resources(resources, error_identifiers)
    if not skip_invalid_resources and resource_errors:
        return [], resource_errors

    saved_resources_pks = []
    errors = []

    for chunk in chunked(valid_resources, chunk_size):
        context = context_mapper(
            model_mapper.to_obj,
            delete_related=delete_related,
            error_identifiers=error_identifiers,
        )

        result = model_mapper.apply(chunk, context=context)

        try:
            instances = list(result)
        except TypeError:  # it is not a list
            instances = [result]

        chunk_saved_resources, chunk_errors = context.bulk_save(
            instances,
            fields_to_update,
            identifier_mapping,
            clean_instances,
        )

        # Don't store all the model instances in saved_resources, as this could lead to memory issues.
        for instance in chunk_saved_resources:
            saved_resources_pks.append(instance.pk)

        errors.extend(chunk_errors)

    saved_resources = model_mapper.to_obj.objects.filter(pk__in=saved_resources_pks)
    return saved_resources, resource_errors + errors
