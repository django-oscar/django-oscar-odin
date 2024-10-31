"""Resources for Oscar categories."""
from oscar.core.loading import get_class

OscarResource = get_class("oscar_odin.resources._base", "OscarResource")


class _User(OscarResource, abstract=True):
    """Base resource for Oscar user application."""

    class Meta:
        allow_field_shadowing = True
        namespace = "oscar.user"


class UserResource(_User):
    """User resource."""

    id: int
    first_name: str
    last_name: str
    email: str
