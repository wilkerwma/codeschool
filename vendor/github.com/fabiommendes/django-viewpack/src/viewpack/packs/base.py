import types
import collections
from django.conf.urls import url, include
from django.views.generic import View
from viewpack.decorators import view
from viewpack.views.mixins import ChildViewMixin
from viewpack.utils import (
    get_app_name, get_view_name, get_url_name, get_pattern, delegate_to_parent
)


class ViewPackMeta(type(View)):
    """
    Metaclass for ViewPack types.
    """

    def __new__(cls, name, bases, namespace):
        new = type.__new__(cls, name, bases, namespace)
        new.__prepare_meta()
        return new

    def __prepare_meta(self):
        """Prepare recently created class."""

        self._meta = Meta()
        self._meta.view_attributes = {}
        self._meta.view_patterns = {}
        self._meta.view_url_names = {}

        # Read all objects and process them
        for attr in dir(self):
            if attr.startswith('_'):
                continue
            obj = getattr(self, attr, None)

            # Process class based views:
            # First we check if there is a Mixin class attribute related to that
            # class. If so, we override the class based view with a composition
            # with its mixin class. The mixin class is always removed after
            # the composition.
            if isinstance(obj, type) and issubclass(obj, View):
                view_cls = obj

                # Create subclass using mixin. We check if there is a mixin
                # either in SomeNameViewMixin or SomeNameMixin attributes.
                basename = attr[:-4] if attr.endswith('View') else attr
                if hasattr(self, basename + 'Mixin'):
                    mixin_name = basename + 'Mixin'
                elif hasattr(self, attr + 'Mixin'):
                    mixin_name = attr + 'Mixin'
                else:
                    mixin_name = None

                if mixin_name:
                    mixin = getattr(self, mixin_name)
                    view_cls = type(attr, (mixin, view_cls), {})
                    setattr(self, attr, view_cls)
                    delattr(self, mixin_name)

                # Create view method for that class
                view_name = get_view_name(view_cls)
                view = view_function_factory(view_cls)
                attr = '_%s__%s' % (self.__name__, view_name)
                setattr(self, attr, view)

            # Mixins are ignored unless there is no view class related to them.
            elif attr.endswith('Mixin'):
                basename = attr[:-5]
                if not (hasattr(self, basename) or
                            hasattr(self, basename + 'View')):
                    fmt = (attr, basename, basename + 'View')
                    raise ValueError(
                        'Mixin class %s, does not have any related class based'
                        'views. Please define either %s or %s views.' % fmt
                    )
                view_attr = basename
                if not hasattr(self, basename):
                    view_attr = basename + 'View'
                view_cls = getattr(self, view_attr)

                if not (isinstance(view_cls, type) and
                            issubclass(view_cls, View)):
                    fmt = (view_attr, view_cls)
                    raise ValueError(
                        '%r should be a View subclass, got: %r' % fmt)

            # Process methods marked with a @view decorator
            elif (isinstance(obj, types.FunctionType) and
                      getattr(obj, 'is_view', False)):

                if hasattr(obj, 'as_view'):
                    obj = obj.as_view()
                    view_name = get_view_name(obj)
                    attr = '_%s__%s' % (self.__name__, view_name)
                    setattr(self, attr, obj)

            # Objects that have an as_view() method are also accepted

            else:
                continue

            view_name = get_view_name(obj)
            self._meta.view_attributes[view_name] = attr
            self._meta.view_patterns[view_name] = get_pattern(obj)
            self._meta.view_url_names[view_name] = get_url_name(obj)


#
# Auxiliary methods and types
#
class Meta:
    """Empty namespace that holds meta information.

    Attributes:
        view_attributes:
            A mapping between view names to their corresponding attributes.
            names.
        view_patterns:
            A mapping between view names to their corresponding url pattern
            strings..
        view_url_names:
            A mapping between view names to the corresponding reverse url names.
    """


def view_function_factory(view_cls):
    """Return a view method for the given class based view."""

    pattern = get_pattern(view_cls)
    url_name = get_url_name(view_cls)
    view_name = get_view_name(view_cls)

    @view(pattern=pattern, view_name=view_name, url_name=url_name)
    def view_method(self, request, *args, **kwargs):
        initargs = self.initkwargs or {}
        view_obj = view_cls(**initargs)
        self.child_view_object = view_obj
        self.init_child(view_obj)
        return view_obj.dispatch(request, *args, **kwargs)

    return view_method


#
# Base class for all view groups
#
class ViewPack(ChildViewMixin, View, metaclass=ViewPackMeta):
    """
    A parent view that dispatches to one child by asking each child if it
    accepts the given request.
    """
    #: Name of the child view that it should dispatch to
    dispatch_to = delegate_to_parent('dispatch_to')

    #: initkwargs that should be passed to class-based child views
    initkwargs = delegate_to_parent('initkwargs')

    #: Instance of the child view object responsible to respond to the request.
    #: This value is method-based, this attribute is set to None.
    child_view_object = None

    def __init__(self, dispatch_to=None, **kwargs):
        self.dispatch_to = dispatch_to
        super().__init__(**kwargs)

    @classmethod
    def as_view(self, dispatch_to=None, initkwargs=None, **initkwargs_):
        """
        Return a child view as a view function.

        Since group views comprises several different sub-views, it necessary
        to tell which view should be chosen. It is probably more convenient to
        register the ViewPack urls using the :func:`ViewPack.as_include`
        class method.

        It accepts two function signatures::

            ViewPack.as_view(view_name, **kwargs)
            ViewPack.as_view(view_name, initkwargs, **kwargs)

        In the first, the kwargs are passed to the ViewPack and in the second
        they are passed to the sub-view, it is a class based view.
        """
        if dispatch_to is None:
            raise RuntimeError(
                'ViewGroups views require a second parameter with the '
                'associated child view.\n'
                'Since they catch multiple urls, it is more convenient to '
                'register the urlpattenrs using ViewPack.as_include():\n')

        view = super().as_view(dispatch_to=dispatch_to,
                               initkwargs=initkwargs,
                               **initkwargs_)
        return view

    @classmethod
    def as_include(cls, initkwargs=None, *, namespace=None):
        """
        Register views as an include urlpatterns

        Example::

            urlpatterns = [
                url(r'^foo/', FooViewGroup.as_include(name='foo')),
            ]

        Args:
            initkwargs:
                A dictionary with the initial keyword args passed to the view
                constructor.
        Keyword args:
            namespace:
                Base name of the view. Each child view is registered by joining
                name with the child view own name.
        """

        app_name = get_app_name(cls)
        patterns = cls.as_include_patterns(initkwargs, app_name=app_name)
        includes = include(URLModule(patterns, app_name), namespace=namespace)
        return includes

    @classmethod
    def as_include_patterns(cls, initkwargs=None, *, prefix=None, app_name=None):
        """
        Return a list of url patterns for view.
        """

        if app_name is None:
            app_name = get_app_name(cls)
        basename = prefix
        patterns = []

        for view, pattern in cls._meta.view_patterns.items():
            if basename:
                prefix = '%s-%s' % (basename, cls._meta.view_url_names[view])
            else:
                prefix = cls._meta.view_url_names[view]
            view_func = cls.as_view(view, **(initkwargs or {}))
            pattern = url(pattern, view_func, name=prefix)
            patterns.append(pattern)

        return patterns

    def init(self, request, *args, **kwargs):
        """
        This method is called to initialize the class-based view with arguments
        passed to the view function before dispatching to the child view.

        The default implementation simply saves each value in the corresponding
        `request`, `args` and `kwargs` attributes.
        """

        self.request = request
        self.args = args
        self.kwargs = kwargs

    def init_child(self, view):
        """
        This method is executed every time a new sub-view view instance is
        created.

        The default implementation simply saves itself in the `parent`
        attribute and saves copy the `request`, `args`, and `kwargs` attributes.
        """

        view.parent = self
        view.request = self.request
        view.args = self.args
        view.kwargs = self.kwargs

    def dispatch(self, request, *args, **kwargs):
        """
        Instantiate each children class and return the first that accepts the
        request.
        """

        self.init(request, *args, **kwargs)

        if self.dispatch_to is not None:
            return self.dispatch_to_child(self.dispatch_to, request)

        raise ImproperlyConfigured(
            'Class must be initialized with the dispatch_to attribute set.'
        )

    def dispatch_to_child(self, view_name, request):
        """
        Dispatch url to the given child view.
        """

        try:
            attr = self._meta.view_attributes[view_name]
        except KeyError:
            raise ValueError('view %r does not exist' % view_name)

        method = getattr(self, attr)
        self.child_view_name = view_name
        return method(request, *self.args, **self.kwargs)


# This object is used to represent a url.py module with a urlpatterns list
URLModule = collections.namedtuple('URLModule', ['urlpatterns', 'app_name'])
