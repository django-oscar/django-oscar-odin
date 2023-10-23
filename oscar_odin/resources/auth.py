"""Resources for Oscar categories."""
from ._base import OscarResource


class _User(OscarResource, abstract=True):
    """Base resource for Oscar user application."""

    class Meta:
        namespace = "oscar.user"


class User(_User):
    """User resource."""

    id: int
    first_name: str
    last_name: str
    email: str
