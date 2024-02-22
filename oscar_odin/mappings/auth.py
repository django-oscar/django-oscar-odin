"""Mappings between odin and django auth models."""
from oscar.core.loading import get_model

from .. import resources
from ._common import OscarBaseMapping

__all__ = ("UserToResource",)

UserModel = get_model("auth", "User")


class UserToResource(OscarBaseMapping):
    """Mapping from user model to resource."""

    from_obj = UserModel
    to_obj = resources.auth.User
