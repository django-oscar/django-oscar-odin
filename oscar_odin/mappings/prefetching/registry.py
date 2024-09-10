from typing import Dict, Any, Union, Callable, List, Set

from django.db.models import Prefetch

from oscar.core.loading import get_class

ProductQuerySet = get_class("catalogue.managers", "ProductQuerySet")

PrefetchType = Union[
    str, Prefetch, Callable[[ProductQuerySet, Dict[str, Any]], ProductQuerySet]
]
SelectRelatedType = Union[str, List[str]]


class PrefetchRegistry:
    """
    This class enables the flexibility to register prefetch_related and select_related operations
    for the product_queryset_to_resources method. By default, django-oscar-odin prefetches all related
    fields that are used by the default mapping.

    However, it's likely that you have your own resource(s) that makes use of the product_queryset_to_resources
    method while doing additional queries. To make it easier to add your own prefetches, to prevent n+1 queries
    you can register your own prefetches and select_related operations.

    You can also unregister default ones, and replace them with your own. For example when your way of
    getting stockrecords does a different query, it's better to unregister the default one and register your own.
    This way, you're also not doing a useless query.
    """

    def __init__(self):
        self.prefetches: Dict[str, PrefetchType] = {}
        self.children_prefetches: Dict[str, PrefetchType] = {}
        self.select_related: Set[str] = set()

    def register_prefetch(self, prefetch: PrefetchType):
        """
        Register a prefetch_related operation.

        Args:
            prefetch (PrefetchType): The prefetch to register. Can be a string, Prefetch object, or a method.
        """
        key = self._get_key(prefetch)
        self.prefetches[key] = prefetch

    def register_children_prefetch(self, prefetch: PrefetchType):
        """
        Register a children prefetch_related operation. Children as is, the children of a parent.

        Args:
            prefetch (PrefetchType): The child prefetch to register. Can be a string, Prefetch object, or a method.
        """
        key = self._get_key(prefetch)
        self.children_prefetches[key] = prefetch

    def register_select_related(self, select: SelectRelatedType):
        """
        Register a select_related operation.

        Args:
            select (SelectRelatedType): The select_related to register. Can be a string or a list of strings.
        """
        if isinstance(select, str):
            self.select_related.add(select)
        elif isinstance(select, list):
            self.select_related.update(select)

    def unregister_prefetch(self, prefetch: Union[str, Callable]):
        """
        Unregister a prefetch_related operation.

        Args:
            prefetch (Union[str, Callable]): The prefetch to remove. Can be a string or a method.
        """
        key = self._get_key(prefetch)
        self.prefetches.pop(key, None)

    def unregister_children_prefetch(self, prefetch: Union[str, Callable]):
        """
        Unregister a children-specific prefetch_related operation. Children as is, the children of a parent.

        Args:
            prefetch (Union[str, Callable]): The child prefetch to remove. Can be a string or a method.
        """
        key = self._get_key(prefetch)
        self.children_prefetches.pop(key, None)

    def unregister_select_related(self, select: str):
        """
        Unregister a select_related operation.

        Args:
            select (str): The select_related to remove.
        """
        self.select_related.discard(select)

    def get_prefetches(self) -> Dict[str, PrefetchType]:
        """
        Get all registered prefetch_related operations.

        Returns:
            Dict[str, PrefetchType]: A dictionary of prefetch keys to their prefetch.
        """
        return self.prefetches

    def get_children_prefetches(self) -> Dict[str, PrefetchType]:
        """
        Get all registered children-specific prefetch_related operations. Children as is, the children of a parent.

        Returns:
            Dict[str, PrefetchType]: A dictionary of child prefetch keys to their prefetch.
        """
        return self.children_prefetches

    def get_select_related(self) -> List[str]:
        """
        Get all registered select_related operations.

        Returns:
            List[str]: A list of select_related fields.
        """
        return list(self.select_related)

    def _get_key(self, operation: Union[PrefetchType, SelectRelatedType]) -> str:
        """
        Get the key for an operation.

        Args:
            operation (Union[PrefetchType, SelectRelatedType]): The operation to get the key for.

        Returns:
            str: The key for the operation.
        """
        if isinstance(operation, str):
            return operation
        elif isinstance(operation, Prefetch):
            return operation.prefetch_to
        elif callable(operation):
            return operation.__name__
        else:
            raise ValueError(f"Unsupported operation type: {type(operation)}")


prefetch_registry = PrefetchRegistry()
