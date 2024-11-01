from oscar_odin.mappings.context import ModelMapperContext
from oscar_odin.utils import validate_resources


def resources_to_db(
    resources,
    fields_to_update,
    identifier_mapping,
    model_mapper,
    delete_related=False,
    clean_instances=True,
    skip_invalid_resources=False,
    error_identifiers=None,
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

    context = ModelMapperContext(
        model_mapper.to_obj,
        delete_related=delete_related,
        error_identifiers=error_identifiers,
    )
    result = model_mapper.apply(valid_resources, context=context)

    try:
        instances = list(result)
    except TypeError:  # it is not a list
        instances = [result]

    saved_resources, errors = context.bulk_save(
        instances,
        fields_to_update,
        identifier_mapping,
        clean_instances,
    )
    return saved_resources, resource_errors + errors
