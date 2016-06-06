import collections
from django.views.generic import base
from django.core.exceptions import ImproperlyConfigured
from django import http
from viewpack.utils import lazy, delegate_to_parent
from viewpack.views import View, TemplateView
from viewpack.views.mixins import SingleObjectMixin, VerboseNamesContextMixin
from viewpack.packs.base import ViewPack, ViewPackMeta, view
from viewpack.packs.crud import CRUDViewPack
__all__ = [
    # Dispatch views
    'DispatchView', 'DispatchViewMixin',

    # Viewpack
    'InheritanceCRUDViewPack'
]


REGEX_CACHE = {}


# Dispatch view simply redirect some view to the subclass CrudView.
class DispatchViewMixin(SingleObjectMixin):
    """Loads object and dispatch to correct subclass."""

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return self.parent.dispatch_to_object(obj, request, *args, **kwargs)

    post = put = get


class DispatchView(DispatchViewMixin, View):
    """A view that implements the DispatchViewMixin."""


# Inheritance CRUD organizes several CRUD view packs for objects of different
# classes
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

    #: A dictionary mapping each model to their respective view pack
    #: class.
    registry = None

    DetailViewMixin = DispatchViewMixin
    UpdateViewMixin = DispatchViewMixin
    DeleteViewMixin = DispatchViewMixin

    class CreateView(VerboseNamesContextMixin,
                     TemplateView):
        """
        Creates a new instances.

        This view require a second parameter that is matched to the
        `subclass_view_type` attribute of a registered child view. The default
        implementation uses urls such as::

            new/<subclass_view_name>/

        in order to delegate to the 'create' subview of the CRUDViewPack
        associated with the given <subclass_view_name> value.
        """

        pattern = r'^new/(?P<subclass_view_name>\w*)/?$'

        def get_context_data(self, **kwargs):
            def get_name(x):
                try:
                    return getattr(x, 'subclass_view_name')
                except:
                    return x.model.__name__.lower()

            L = self.parent.get_subpack_list()
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

            return self.parent.get_pack(subclass_view_name)

    # class ExtraActionView(SingleObjectMixin, View):
    #     """Captures any other sub-url and try to dispatch to some registered
    #     class."""
    #
    #     pattern = r'^(?P<pk>\d+)/(?P<url>.*)$'
    #
    #     def match_url(self, pack, url):
    #         """Searches all subviews for a matching url."""
    #
    #     def dispatch(self, request, pk, url):
    #         self.object = self.get_object()
    #         pack = self.get_pack(type(self.object))
    #         subview = self.match_url(pack, url)
    #         return self.process_subview(subvview)

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

    def get_pack(self, value):
        """Return the child CRUDViewPack instance associated with the
        given name or type."""

        # This function accepts either a string with the pack name or a type
        if isinstance(value, str):
            for child_cls in self.registry.values():
                name = getattr(child_cls, 'subclass_view_name', None)
                if isinstance(name, str):
                    if name == value:
                        return self.init_subclass_view(child_cls)
                    continue
                child = self.init_subclass_view(child_cls)

                # If subclass_view_name is not defined, we compute it from the
                # lowercase version of the model name.
                if name is None:
                    name = child.model.__name__.lower()
                if name == value:
                    return child
            raise ValueError('invalid subclass_view_name: %r' % value)

        # Search by type
        #for child_cls in self.

    def get_subpack_list(self):
        """
        Return a list with all registered subclass views objects.

        Each view is initialized as if it would have been if executed with the
        dispatch method.
        """

        L = []
        for child_cls in self.registry.values():
            child = self.init_subclass_view(child_cls)
            L.append(child)
        return L

    def get_subpack_models(self):
        """
        Return a list with all (subclass_view_name, model) items.
        """
        return [
            (pack.subclass_view_name, model)
            for (model, pack) in self.registry.items()
        ]

    @classmethod
    def register(cls, viewpack=None, *, model=None, as_fallback=False, force=False):
        """
        Register the given viewgroup for objects of the given type.

        Can be used as a decorator.

        Args:
            viewpack:
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
        if viewpack is None:
            return lambda viewpack: cls.register(
                viewpack, model=model, as_fallback=as_fallback, force=force
            )

        # Retrieves model from view, if necessary
        if as_fallback:
            model = None
        elif model is None:
            model = viewpack.model

        # Register
        if force and model in cls.registry:
            if model is None:
                raise ImproperlyConfigured(
                    'Fallback view is already registered'
                )
            raise ImproperlyConfigured(
                'A view is already registered for model: %s' % model.__name__
            )
        cls.registry[model] = viewpack

        return viewpack

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
