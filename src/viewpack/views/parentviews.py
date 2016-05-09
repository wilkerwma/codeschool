import collections
from django.views.generic import base
from django.core.exceptions import ImproperlyConfigured
from django import forms
from django import http
from viewpack.utils import lazy
from viewpack.views import ViewPack
from viewpack.views.base import ViewPackMeta
from viewpack.views.childviews import (
    View,
    DetailView,
    CreateView,
    ListView,
    DeleteView,
    UpdateView,
    VerboseNamesContextMixin,
    DetailObjectContextMixin,
    TemplateResponseMixin,
    TemplateView,
    SingleObjectMixin,
    delegate_to_parent
)


#
# Parent mixins
#
class SingleObjectParentMixin(SingleObjectMixin):
    @lazy
    def object(self):
        # Retrieve from parent
        if self.parent is not None:
            object = getattr(self.parent, 'object', None)
            if object is not None:
                return object

        # Get it from get_object()
        try:
            return self.get_object()
        except AttributeError:
            return None


class TemplateResponseParentMixin(TemplateResponseMixin):
    template_basename = delegate_to_parent('template_basename')
    template_extension = delegate_to_parent('template_extension', '.html')

    @property
    def template_extension_normalized(self):
        """
        Normalized template extension.

        An empty extension remains empty. Other extensions are normalized to
        start with a dot.
        """
        template_extension = self.template_extension
        if template_extension:
            template_extension = '.' + template_extension.lstrip('.')
        return template_extension

    def get_template_names(self, view_name):
        # Try default implementation that relies on the variable template_name
        # being set.
        try:
            names = super().get_template_names()
        except ImproperlyConfigured:
            if self.template_basename is None:
                raise
            names = []

        # Now we construct a template name from the given view_name and template
        # extension.
        if self.template_basename:
            names.append('%s%s%s' % (
                self.template_basename,
                view_name,
                self.template_extension_normalized
            ))

        return names


#
# Simple reusable CRUD interface
#
class CRUDViewPack(SingleObjectParentMixin, TemplateResponseParentMixin, ViewPack):
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
                     CreateView):
        pattern = r'^new/$'

    class DetailView(DetailObjectContextMixin,
                     VerboseNamesContextMixin,
                     DetailView):
        pattern = r'(?P<pk>\d+)/$'

    class UpdateView(DetailObjectContextMixin,
                     VerboseNamesContextMixin,
                     UpdateView):
        pattern = r'^(?P<pk>\d+)/edit/$'
        success_url = '../'

    class DeleteView(DetailObjectContextMixin,
                     VerboseNamesContextMixin,
                     DeleteView):
        pattern = r'^(?P<pk>\d+)/delete/$'

    class ListView(VerboseNamesContextMixin, ListView):
        pattern = r'^$'


#
# CRUD with subclass dispatch
#
class DispatchViewMixin(SingleObjectMixin):
    """Loads object and dispatch to correct subclass."""

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return self.parent.dispatch_to_object(obj, request, *args, **kwargs)

    post = put = get


class DispatchView(DispatchViewMixin, View):
    """A view that implements the DispatchViewMixin."""


class InheritanceCRUDViewPackMeta(ViewPackMeta):
    """
    Metaclass for InheritanceCRUDViewPack
    """
    def __new__(cls, name, bases, ns):
        try:
            InheritanceCRUDViewPack
        except NameError:
            pass
        else:
            if 'model' not in ns:
                raise ImproperlyConfigured(
                    'InheritanceCRUDViewPack subclasses must define a '
                    'model attribute'
                )

        new = ViewPackMeta.__new__(cls, name, bases, ns)
        new.registry = collections.OrderedDict()
        return new


class InheritanceCRUDViewPack(CRUDViewPack,
                              metaclass=InheritanceCRUDViewPackMeta):
    """Similar to ViewPack, but it dispatch to different sub-cruds depending
     on the type of the requested object.

     Each sub-crud class might define a subclass_view_name attribute that is
     used to map each subclass with the corresponding name in the
     ``/new/<subclass_view_name>`` urls.
     """

    #: Type used for dispatch.
    subclass_view_type = delegate_to_parent('subclass_view_type')
    DetailViewMixin = DispatchViewMixin
    UpdateViewMixin = DispatchViewMixin
    DeleteViewMixin = DispatchViewMixin

    class CreateView(VerboseNamesContextMixin,
                     TemplateView):
        pattern = r'^new/(?P<subclass_view_name>\w*)/?$'

        def get_context_data(self, **kwargs):
            def get_name(x):
                try:
                    return getattr(x, 'subclass_view_name')
                except:
                    return x.model.__name__.lower()

            L = self.parent.get_subclass_views_list()
            L = [(get_name(x), x) for x in L]
            return super().get_context_data(name_view_list=L, **kwargs)

        def dispatch(self, request, *args, subclass_view_name=None, **kwargs):
            if not subclass_view_name:
                self.view_name = 'create-list'
                return super().dispatch(request, *args, **kwargs)

            view = self.get_subclass_view(subclass_view_name)
            return view.dispatch(request, *args, **kwargs)
        
        def get_subclass_view(self, subclass_view_name):
            """Return the child CRUDViewPack instance associated with the
            given child_view_name."""

            return self.parent.get_subclass_view(subclass_view_name)

    def init_subclass_view(self, cls):
        """Initialize an instance of a child view pack class."""

        return cls(
            dispatch_to=self.dispatch_to,
            initkwargs=self.initkwargs,
            parent=self,
            request=self.request,
            args=self.args,
            kwargs=self.kwargs,
            **(self.initkwargs or {})
        )

    def get_subclass_view(self, subclass_view_name):
        """Return the child CRUDViewPack instance associated with the
        given child_view_name."""

        for child_cls in self.registry.values():
            name = getattr(child_cls, 'subclass_view_name', None)
            if isinstance(name, str):
                if name == subclass_view_name:
                    return self.init_subclass_view(child_cls)
                continue
            child = self.init_subclass_view(child_cls)

            # If subclass_view_name is not defined, we compute it from the
            # lowercase version of the model name.
            if name is None:
                name = child.model.__name__.lower()
            if name == subclass_view_name:
                return child
        raise ValueError('invalid subclass_view_name: %r' % subclass_view_name)

    def get_subclass_views_list(self):
        """Return a list with all registered subclass views objects.

        Each view is initialized as if it would have been if executed with the
        dispatch method."""

        L = []
        for child_cls in self.registry.values():
            child = self.init_subclass_view(child_cls)
            L.append(child)
        return L

    @classmethod
    def register(cls, viewgroup=None, *, model=None, as_fallback=False, force=False):
        """
        Register the given viewgroup for objects of the given type.

        Can be used as a decorator.

        Args:
            viewgroup:
                Registered class
            model:
                Optional model type associated to the group. If not givem
                it uses viewgroup.model.
            as_fallback:
                If true, register viewgroup as the fallback view for objects of
                non-registered types.
            force:
                Forces registration of an existing type.
        """

        # Decorator form
        if viewgroup is None:
            return lambda viewgroup: cls.register(
                viewgroup, model=model, as_fallback=as_fallback, force=force
            )

        # Retrieves model from view, if necessary
        if as_fallback:
            model = None
        elif model is None:
            model = viewgroup.model

        # Register
        if force and model in cls.registry:
            if model is None:
                raise ImproperlyConfigured(
                    'Fallback view is already registered'
                )
            raise ImproperlyConfigured(
                'A view is already registered for model: %s' % model.__name__
            )
        cls.registry[model] = viewgroup

        return viewgroup

    def get_queryset(self):
        """
        Returns the queryset.

        If manager has a select_subclasses() method (as in Django model util's
        InheritanceManager), it uses this method.
        """

        queryset = super().get_queryset()
        if hasattr(queryset, 'select_subclasses'):
            return queryset.select_subclasses()
        return queryset

    def dispatch_to_object(self, object, request, *args, **kwargs):
        """
        Dispatch to the sub-view that is responsible for dealing with input
        object.
        """

        cls = type(object)
        try:
            view_cls = self.registry[cls]
        except KeyError:
            if None in self.registry:
                view_cls = self.registry[None]
            raise http.Http404('No view registered to %s objects' % cls.__name__)

        # We now create a view object and dispatch to it
        self.subclass_view_type = cls
        self.child_view_object = view_cls(parent=self,
                                          object=object,
                                          dispatch_to=self.child_view_name)
        return self.child_view_object.dispatch(request, *args, **kwargs)
