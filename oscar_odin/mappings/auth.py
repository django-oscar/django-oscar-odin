"""Mappings between odin and django auth models."""
from oscar.core.loading import get_model, get_class

__all__ = ("UserToResource",)

UserModel = get_model("auth", "User")

# mappings
OscarBaseMapping = get_class("oscar_odin.mappings._common", "OscarBaseMapping")

# resources
UserResource = get_class("oscar_odin.resources.auth", "UserResource")


class UserToResource(OscarBaseMapping):
    """Mapping from user model to resource."""

    from_obj = UserModel
    to_obj = UserResource
