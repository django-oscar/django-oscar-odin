"""Mappings between odin and django auth models."""
import odin
from oscar.core.loading import get_model

from .. import resources

__all__ = ("UserToResource",)

UserModel = get_model("auth", "User")


class UserToResource(odin.Mapping):
    """Mapping from user model to resource."""

    from_obj = UserModel
    to_obj = resources.auth.User
