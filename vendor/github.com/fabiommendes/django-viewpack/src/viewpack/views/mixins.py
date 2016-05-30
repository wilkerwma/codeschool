"""
Gather all mixin classes defined in other modules.
"""
from .base import (
    ChildViewMixin,
    ParentContextMixin,
    ContextMixin,
    TemplateResponseEndpointMixin,
    ParentTemplateNamesMixin,
    TemplateResponseMixin,
)
from .detail import (
    SingleObjectMixin,
    SingleObjectTemplateResponseMixin,
)
from .edit import (
    FormMixin, ModelFormMixin, DeletionMixin
)
from .extra import (
    VerboseNamesContextMixin, DetailObjectContextMixin, DetailWithResponseView,
    HasUploadMixin,
)