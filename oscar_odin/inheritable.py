from typing import Type

from odin.annotated_resource import AnnotatedResourceType
from odin.fields import NotProvided
from odin.resources import ResourceBase, ResourceType, ResourceOptions, MOT


class InheritableResourceOptions(ResourceOptions):
    """
    odin heavily caches resources. It does this by adding a resource to a resource
    registry the minute the resource gets initiated (__new__) --> metaclass.

    The cache/registry key is from the resource name(classname) and name_space (meta) combined.
    However, when a resource inherits from another resource, the namespace also gets inherited.

    This is problematic in context of oscar's `get_class` method, as the class name will be the same
    and since namespaces are inherited, this will also be the same. This results in odin returning the old resource class from
    the cache / registry.

    This class sets the namespace to NotProvided, odin will in this case generate the namespace
    from the module where the resource is defined. This will make sure that the namespace is unique
    for each resource, even if they inherit from each other.
    """

    def inherit_from(self, base):
        super().inherit_from(base)
        self.name_space = NotProvided


class InheritableResourceType(ResourceType):
    meta_options = InheritableResourceOptions


class InheritableResourceBase(ResourceBase):
    pass


class InheritableAnnotatedResourceType(AnnotatedResourceType):
    def __new__(
        mcs,
        name: str,
        bases,
        attrs: dict,
        # Set our inheritable meta options type
        meta_options_type: Type[MOT] = InheritableResourceOptions,
        abstract: bool = False,
    ):
        return super().__new__(mcs, name, bases, attrs, meta_options_type, abstract)


class Resource(InheritableResourceBase, metaclass=InheritableResourceType):
    """
    from oscar_odin.resources.inheritable import Resource
    class MyResource(Resource):
        pass
    """


class AnnotatedResource(
    InheritableResourceBase,
    metaclass=InheritableAnnotatedResourceType,
    meta_options_type=InheritableResourceOptions,
):
    """
    from oscar_odin.resources.inheritable import AnnotatedResource
    class MyAnnotatedResource(AnnotatedResource):
        pass
    """
