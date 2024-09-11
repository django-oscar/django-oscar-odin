"""Common base resource for all Oscar resources."""
import odin


class OscarResource(odin.AnnotatedResource, abstract=True):
    """Base resource for Oscar models."""

    @property
    def model_instance(self):
        return self._model_instance

    @model_instance.setter
    def model_instance(self, value):
        self._model_instance = value

    def extra_attrs(self, attrs):
        model_instance = attrs.get("model_instance")
        if model_instance is not None:
            self.model_instance = model_instance

    class Meta:
        allow_field_shadowing = True
        namespace = "oscar"
