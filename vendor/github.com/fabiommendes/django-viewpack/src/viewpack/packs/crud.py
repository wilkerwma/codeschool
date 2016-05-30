from django import forms
from django.core.exceptions import ImproperlyConfigured
from viewpack.packs import (
    ViewPack, SingleObjectPackMixin, TemplateResponsePackMixin
)
from viewpack.views import (
    View, DetailView, CreateView, ListView, DeleteView, UpdateView, TemplateView
)

from viewpack.views.mixins import (
    VerboseNamesContextMixin, DetailObjectContextMixin, TemplateResponseMixin,
    HasUploadMixin, SingleObjectMixin,
)
from viewpack.utils import lazy, delegate_to_parent


class CRUDViewPack(SingleObjectPackMixin,
                   TemplateResponsePackMixin,
                   ViewPack):
    """
    A view group that defines a CRUD interface to a model.

    It handles the following urls::

        /               --> list view
        new/            --> creates a new object
        <pk>/           --> detail view
        <pk>/edit/      --> edit object
        <pk>/delete/    --> delete object


    Each one of these entry points is controlled by a specific View inner class:

        * :class:`viewgoups.CRUDViewPack.ListView`: index listings
        * :class:`viewgoups.CRUDViewPack.CreateView`: create new objects
        * :class:`viewgoups.CRUDViewPack.DetailView`: show object's detail
        * :class:`viewgoups.CRUDViewPack.EditView`: edit object.
        * :class:`viewgoups.CRUDViewPack.DeleteView`: delete an object.

    It is possible to disable any view by setting the corresponding attribute to
    None in a subclass. One can completely replace theses view classes by their
    own views or, more conveniently, implement mixin classes that are
    automatically used during class creation::


        class MyCRUD(CRUDViewPack):
            model = MyModel

            # Disable list views
            ListView = None

            # Mixin class that is mixed with the default CreateView class
            class CreateViewMixin:
                pattern = r'^create/$'

    """
    CRUD_VIEWS = {'create', 'detail', 'update', 'delete', 'list'}

    #: List of fields that should be excluded from the model forms automatically
    #: generated in the child views. Can be used as an alternative to the
    # `fields` attribute in order to create a blacklist.
    exclude_fields = delegate_to_parent('exclude_fields', None)

    @lazy
    def fields(self):
        """Define a list of fields that are used to automatically create forms
        in the update and create views."""

        if self.exclude_fields is None:
            return forms.fields_for_model(self.model)
        else:
            exclude = self.exclude_fields
            return forms.fields_for_model(self.model, exclude=exclude)

    #: If True, the generic crud templates are not included in the list of
    #: template for child views.
    disable_crud_templates = delegate_to_parent('disable_crud_templates', False)

    #: If True (default), if will use the functions in
    # :mod:`viewpack.permissions` to check if the user has permissions to view,
    # edit or create new objects.
    check_permissions = delegate_to_parent('check_permissions', False)

    def get_template_names(self, view_name):
        assert isinstance(view_name, str), 'invalid view name: %r' % view_name

        try:
            names = super().get_template_names(view_name)
        except ImproperlyConfigured:
            if ((not self.disable_crud_templates) or
                    (view_name not in self.CRUD_VIEWS)):
                raise
            names = []

        # We add the default views to the search list of valid views
        if not self.disable_crud_templates and view_name in self.CRUD_VIEWS:
            names.append(
                'viewpack/crud/%s%s' % (
                    view_name, self.template_extension_normalized
                ))
            names.append(
                'viewpack/crud/%s-base%s' % (
                    view_name, self.template_extension_normalized
                ))
        return names

    class CreateView(VerboseNamesContextMixin,
                     HasUploadMixin,
                     CreateView):
        """Create new objects."""

        pattern = r'^new/$'

    class DetailView(DetailObjectContextMixin,
                     VerboseNamesContextMixin,
                     DetailView):
        """Detail view for object."""

        pattern = r'(?P<pk>\d+)/$'

    class UpdateView(DetailObjectContextMixin,
                     VerboseNamesContextMixin,
                     UpdateView):
        """Edit object."""

        pattern = r'^(?P<pk>\d+)/edit/$'
        success_url = '../'

    class DeleteView(DetailObjectContextMixin,
                     VerboseNamesContextMixin,
                     DeleteView):
        """Delete object."""

        pattern = r'^(?P<pk>\d+)/delete/$'

    class ListView(VerboseNamesContextMixin, ListView):
        """List instances of the given model."""

        pattern = r'^$'