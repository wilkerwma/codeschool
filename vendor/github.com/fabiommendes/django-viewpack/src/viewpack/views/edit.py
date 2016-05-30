from django.views.generic import edit
from viewpack.views.utils import check_mro
from viewpack.utils import lazy, delegate_to_parent
from viewpack.views.detail import (
    ChildViewMixin,
    TemplateResponseMixin,
    SingleObjectMixin,
    SingleObjectTemplateResponseMixin
)
from viewpack.views.permission import CanEditMixin, CanCreateMixin


@check_mro
class FormMixin(ChildViewMixin, edit.FormMixin):
    """
    A mixin that provides a way to show and handle a form in a request.
    """


@check_mro
class ModelFormMixin(FormMixin, SingleObjectMixin, edit.ModelFormMixin):
    """
    A mixin that provides a way to show and handle a modelform in a request.
    """

    fields = delegate_to_parent('fields')


@check_mro
class FormView(TemplateResponseMixin, edit.FormView):
    """
    A view for displaying a form, and rendering a template response.
    """


@check_mro
class CreateView(SingleObjectTemplateResponseMixin, ModelFormMixin,
                 edit.CreateView):
    """
    View for creating a new object instance, with a response rendered by
    template.
    """
    template_name_suffix = delegate_to_parent('template_name_suffix', '_form')


@check_mro
class UpdateView(CanEditMixin,
                 SingleObjectTemplateResponseMixin,
                 ModelFormMixin,
                 edit.UpdateView):
    """
    View for updating an object, with a response rendered by template.

    If the attribute ``check_permissions = True``, it will also use the
    functions on :mod:`viewpack.permissions` to grant the edit permission to
    users.
    """


@check_mro
class DeletionMixin(ChildViewMixin, edit.DeletionMixin):
    """
    A mixin providing the ability to delete objects
    """


@check_mro
class DeleteView(CanEditMixin,
                 SingleObjectTemplateResponseMixin,
                 SingleObjectMixin,
                 edit.DeleteView):
    """
    View for deleting an object retrieved with `self.get_object()`, with a
    response rendered by template.

    If the attribute ``check_permissions = True``, it will also use the
    functions on :mod:`viewpack.permissions` to grant the edit permission to
    users.
    """