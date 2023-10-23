"""Resources for Oscar Odin."""

from . import address, auth, catalogue, order
from ._base import OscarResource

__all__ = ["OscarResource", "address", "catalogue", "order", "auth"]
