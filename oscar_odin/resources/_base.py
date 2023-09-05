"""Common base resource for all Oscar resources."""
import odin


class OscarResource(odin.AnnotatedResource, abstract=True):
    """Base resource for Oscar models."""

    class Meta:
        namespace = "oscar"
