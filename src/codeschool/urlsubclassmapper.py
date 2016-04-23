from collections import UserDict, MutableMapping
import copy
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured
from django.conf.urls import url
from django import http
from django import forms
from django.views import generic as generic_views
from codeschool.shortcuts import redirect, lazy
from codeschool.decorators import login_required

__all__ = ['URLSubclassMapper', 'ViewMapper', 'auto_form']


class URLSubclassMapper(UserDict):
    """Maps a CRUD URL interface to a model with sub-models.

    This is used when the URL interface for CRUD-like actions should dispatch
    to different views depending on the type of the related objects. It assumes
    a hierarchy of:

        baseurl/<pk>/           --> detail view
        baseurl/<pk>/<action>   --> do some action in object
        baseurl/new/<subtype>   --> create a new object of the given subtype.
        baseurl/new/            --> page that asks the user to choose the
                                    subtype.

    URLSubclassMapper are initialized with a InheritanceManager instance or
    queryset.
    """

    def __init__(self, manager):
        if not hasattr(manager, 'get_subclass'):
            raise TypeError('URLSubclassMapper expect inheritance managers '
                            'that implement the get_subclass() interface, got: '
                            '%r' % manager)
        self.manager = manager
        super().__init__()

    def register(self, *args, detail=None, new=None, decorator=login_required, **kwargs):
        """
        Register question type.

        Example
        -------

        Can be used as a decorator::

            mapper = URLSubclassMapper(MyModel.objects)

            @mapper.register(model=MySubModel, name='sub')
            class MySubModelViews:
                def new(self, request):
                    do something in here

        or as a regular function call::

           mapper.register(MySubModel, name, MySubModelViews, action=view_func)

        The second signature permits to register different actions implemented
        as separate view functions.
        """

        # Decorator form
        if len(args) == 0:
            try:
                name = kwargs.pop('name', None)
                model = kwargs.pop('model')
            except KeyError:
                raise TypeError('must provide *model* and *name* parameters in '
                                'decorator form')
            if kwargs:
                raise TypeError('invalid keyword argument: %s' %
                                kwargs.popitem()[0])

            def decorator(cls):
                nonlocal name

                if name is None:
                    name = cls.name
                self.register(model, name, cls)
                return cls

            return decorator

        model, name, *args = args
        view_class = args[0] if args else None

        if view_class:
            if not hasattr(view_class, 'name'):
                view_class.name = name
            if not hasattr(view_class, 'model'):
                view_class.model = model

        if view_class:
            for action in dir(view_class):
                if (not action.startswith('view_')) or \
                            getattr(view_class, action) is None:
                    continue

                action = action[5:]
                if action == 'new' and not new:
                    new = decorator(view_class.as_view('new'))
                elif action == 'detail' and not detail:
                    detail = decorator(view_class.as_view('detail'))
                else:
                    view = decorator(view_class.as_view(action))
                    kwargs[action.replace('_', '-')] = view

        kwargs.update(new=new, detail=detail)
        mapping = {k: v for (k, v) in kwargs.items() if v is not None}
        self[model] = mapping
        self[name] = mapping

    def detail(self, request, pk):
        """Generic view that dispatch to the detail page for a given
        question."""

        try:
            obj = self.manager.get_subclass(pk=pk)
        except ObjectDoesNotExist:
            raise http.Http404

        try:
            method = self[type(obj)]['detail']
        except KeyError:
            raise http.Http404
        return method(request, obj)

    def action(self, request, pk, action, **kwds):
        """Generic view that dispatch to some specific action."""

        action, *args = action.split('/')
        try:
            obj = self.manager.get_subclass(pk=pk)
        except ObjectDoesNotExist:
            raise http.Http404('no question with pk=%s found.' % pk)

        try:
            method = self[type(obj)][action]
        except KeyError:
            raise http.Http404
        return method(request, obj, *args)

    def new(self, request, type_name, **kwds):
        """Dispatch to a page for creating new objects."""

        try:
            method = self[type_name]['new']
        except KeyError:
            raise http.Http404
        return method(request)

    def urlpatterns(self, name, patterns=()):
        """Creates an urlpatterns list and optionally prepend it with the
        given additional patterns.

        Name is the used to create the reverse urls lookups '<name>-detail',
        '<name>-action' and '<name>-new'.
        """

        urlpatterns = []
        urlpatterns.extend(patterns)
        urlpatterns.extend([
            url('^(\d+)/$', self.detail, name=name + '-detail'),
            url('^(\d+)/([a-z0-9-/]+)/$', self.action, name=name + '-action'),
            url('^new/([a-z0-9-]+)/$', self.new, name=name + '-new'),
        ])
        return urlpatterns

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)


class MultiViewsMeta(type):
    """Meta class for MultiViews class-based views."""

    def __new__(cls, name, bases, ns):
        abstract = ns.pop('abstract', False)
        new = type.__new__(cls, name, bases, ns)
        if not abstract:
            new.decorate()
        return new

    def decorate(cls):
        """Register classes from models."""

        model = cls.model
        if model is None:
            raise TypeError(
                'must define a model attribute.\n'
                '   Abstract classes should define abstract=True.')
        model_name = model.__name__
        global_mixin = () if cls.mixin is None else (cls.mixin,)

        # Create class-based views classes
        for name in ['list', 'create', 'edit', 'detail', 'action']:
            # Prepare base class
            base = getattr(cls, '%s_view_cls' % name, None)
            if base is not None and not isinstance(base, type):
                continue
            base = base or getattr(type(cls), name.title() + 'View')

            # Get mixins
            mixin = getattr(cls, name + '_mixin', None)
            mixins = tuple(getattr(cls, name + '_mixins', ()))
            if mixin is not None:
                mixins = (mixin,) + mixins

            # Compute bases
            bases = mixins + global_mixin + (base,)

            # Compute extra namespace
            ns = {'manager_cls': cls}
            ns.update(cls.get_namespace_for(name, bases))

            # Create class
            tname = '%s%sView' % (model_name, name.title())
            setattr(cls, '%s_view_cls' % name, type(tname, bases, ns))

    def get_namespace_for(cls, name, bases):
        """Dispatch to the correct namespace initialization function."""

        method = getattr(cls, 'get_namespace_for_' + name, None)
        if method is None:
            return {}
        else:
            return method(bases)

    def get_namespace_for_create(cls, bases):
        """
        Return the prepared namespace for the "create" view.
        """
        return cls.get_field_definition_namespace(bases)

    def get_namespace_for_edit(cls, bases):
        """
        Return the prepared namespace for the "edit" view.
        """
        return cls.get_field_definition_namespace(bases)

    def get_field_definition_namespace(cls, bases):
        """
        Namespace for the fields defined by the `fields` or `exclude` class
        attributes.
        """
        fields = cls.getattr(bases, 'fields', None)
        exclude = cls.getattr(bases, 'exclude', None)

        if fields is None and exclude is None:
            fields = getattr(cls, 'fields', None)
            exclude = getattr(cls, 'exclude', None)

        if fields:
            pass
        elif exclude:
            fields = forms.fields_for_model(cls.model, exclude=exclude)
        else:
            fields = forms.fields_for_model(cls.model, exclude=[])

        return {'fields': list(fields)}

    def getattr(cls, bases, attr, *args):
        """Return an attribute from the list of bases."""

        for base in bases:
            if hasattr(base, attr):
                return getattr(base, attr)
        if args:
            return args[0]
        else:
            raise AttributeError(attr)

    #
    # Define inner class based views
    #
    class MultiViewsMixin:
        """
        Base mixin class that is always applied to all views.
        """
        manager = None

        def _make_name(self, base, file, ext):
            if base.endswith('/'):
                return base + file + ext
            else:
                return '%s_%s%s' % (base, file, ext)

        @property
        def template_name(self):
            return self._make_name(self.manager.template_base,
                                   self.template_file,
                                   self.manager.template_ext)

        def get_template_names(self):
            """
            List of all suitable templates.
            """

            L = [self.template_name]
            for parent in self.manager.get_all_parents():
                L.append(self._make_name(parent.template_base,
                                         self.template_file,
                                         parent.template_ext))
            L.append('multi-views/%s.jinja2' % self.template_file)
            return L

        @property
        def context_object_name(self):
            return self.manager.get_context_object_name()

        def get_context_data(self, **kwargs):
            """
            Adds manage.get_context_globals() to context data.
            """

            context = self.manager.get_context_globals()
            context.update(super().get_context_data(**kwargs))

            # Write all incarnations of object name
            obj = self.object
            for parent in self.manager.get_all_parents():
                context.setdefault(parent.get_context_object_name(), obj)
            return context

        @lazy
        def object(self):
            return self.manager.object

        @lazy
        def model(self):
            return self.manager_cls.model

        def get_object(self, queryset=None):
            if self.object is not None:
                return self.object
            else:
                return super().get_object(queryset=queryset)

        def get_success_url(self):
            try:
                return super().get_success_url()
            except ImproperlyConfigured:
                url = self.request.get_full_path()
                redirect_url, _, _ = url.rpartition('edit')
                if url == redirect_url:
                    raise
                return redirect_url

        args = lazy(lambda s: s.manager.args)
        kwargs = lazy(lambda s: s.manager.kwargs)
        request = lazy(lambda s: s.manager.request)
        can_edit = property(lambda s: s.manager.can_edit)
        can_view = property(lambda s: s.manager.can_view)
        can_create = property(lambda s: s.manager.can_create)
        can_do_action = property(lambda s: s.manager.can_do_action)
        copy_object = property(lambda s: s.manager.copy_object)
        get_object_ref = property(lambda s: s.manager.get_object_ref)

    class ListView(MultiViewsMixin, generic_views.ListView):
        """
        Base class for the "list" view.
        """

        template_file = 'list'

    class CreateView(MultiViewsMixin, generic_views.CreateView):
        """
        Base class for the "create" view.
        """

        template_file = 'create'

        def form_valid(self, form):
            response = super().form_valid(form)
            action = self.request.POST.get('action')
            urlbase = self.request.get_full_path().rpartition('/new')[0]

            if action == 'save':
                return redirect('%s/%s/edit' % (urlbase, self.object.pk))
            return redirect('%s/%s/' % (urlbase, self.object.pk))

    class EditView(MultiViewsMixin, generic_views.UpdateView):
        """
        Base class for the "edit" view.
        """

        template_file = 'edit'

        def form_valid(self, form):
            response = super().form_valid(form)
            action = self.request.POST.get('action')

            if action == 'save':
                return redirect('.')
            elif action == 'copy':
                self.object = self.copy_object(self.object)
                return redirect('../%s/edit' % self.object.pk)
            elif action == 'delete':
                self.object.delete()
                return redirect('../new')
            return response

    class DetailView(MultiViewsMixin, generic_views.DetailView):
        """
        Base class for the "detail" view.
        """

        template_file = 'detail'

    class ActionView(MultiViewsMixin, generic_views.View):
        """
        Base class for all "action" based views.
        """

        template_file = 'action'


class MultiViews(generic_views.View, metaclass=MultiViewsMeta):
    """
    Base class for a simple CRUD-based url interface.

    It handles the following urls:

        baseurl/<pk>/           --> detail view
        baseurl/<pk>/edit       --> edit object
        baseurl/<pk>/<action>   --> do some action in object
        baseurl/new/<subtype>   --> create a new object of the given subtype.
        baseurl/new/            --> page that asks the user to choose the
                                    subtype.
    """

    abstract = True
    parent = None
    model = None
    baseurl = None
    template_ext = '.jinja2'
    mixin = None
    list_mixin = None
    create_mixin = None
    edit_mixin = None
    detail_mixin = None
    action_mixin = None
    import_file = None

    # Default global functions
    context_globals = {}

    @property
    def template_base(self):
        return '%s/%s' % (self.model._meta.app_label, self.short_name)

    @property
    def short_name(self):
        return self.model.__name__.lower()

    @lazy
    def object(self):
        if self.parent is not None:
            return self.parent.object

    @lazy
    def args(self):
        if self.parent is not None:
            return self.parent.args
        return ()

    @lazy
    def kwargs(self):
        if self.parent is not None:
            return self.parent.kwargs
        return {}

    @lazy
    def request(self):
        return self.parent.request

    def __init__(self, object=None, **kwds):
        self.object = object
        super().__init__(**kwds)

    def get_object(self, *args):
        """
        Return the object with the given pk.

        Subclasses may want to override this method in order to fetch objects
        by a different criteria than the primary key.
        """

        return self.model.objects.get(pk=args[0])

    def get_context_object_name(self):
        """
        Return the context name for self.object.
        """

        try:
            return self.context_object_name
        except AttributeError:
            return self.model.__name__.lower()

    def get_object_ref(self, obj=None):
        """Return the slug/pk or url reference to the object."""

        if obj is None:
            obj = self.object
        return obj.pk

    def get_context_globals(self):
        """Return a dictionary with all globals that should be included in the
        context. The globals never overwrite an existing context variable."""

        globals = {
            'detail_object': DetailObject(self),
            'can_edit': LazyBool(lambda: self.can_edit(self.request.user))
        }
        if self.context_globals:
            globals.update(self.context_globals)
        return globals

    def get_initkwargs(self, view_name):
        """Return a dictionary of keyword arguments for the given view."""

        return {}

    def get_all_parents(self):
        """Return a dictionary of keyword arguments for the given view."""

        L = []
        parent = self.parent
        while parent is not None:
            L.append(parent)
            parent = parent.parent
        return L

    def can_view(self, user):
        """Return True if user can view object."""

        if hasattr(self.object, 'can_view'):
            return self.object.can_view(user)
        else:
            return True

    def can_edit(self, user):
        """Return True if user can edit object."""

        if hasattr(self.object, 'can_edit'):
            return self.object.can_edit(user)
        else:
            return user.is_superuser

    def can_create(self, user):
        """Return True if user can edit object."""

        if hasattr(self.object, 'can_create'):
            return self.object.can_edit(user)
        else:
            return self.can_edit(user)

    def can_do_action(self, action, user):
        """Return True if user can perform the given action."""

        method_name = 'can_do_%s' % action
        method = getattr(self, method_name, None)
        method = method or getattr(self.object, method_name, None)
        if method is not None:
            return method(user)
        else:
            return True

    def copy_object(self, object, submit=True):
        """
        Return a copy of the given object.

        If ``submit=False``, it will not save the object to the database.
        """

        object = copy.copy(object)
        object.pk = None

        if submit:
            object.save()
        return object

    def dispatch(self, request, url_args, **kwargs):
        """
        Dispatch to the correct sub-view.
        """

        # Normalize arguments and split them into forward slashes
        args = url_args.split('/')
        if args[-1] == '':
            args.pop()
        if args:
            action, *args = args
        else:
            action = 'list'

        # We want to create the view instances on our own
        subview = self.subview_factory
        self.args = args
        self.kwargs = kwargs
        self.request = request

        # Now we dispatch to the correct class based view by creating an
        # isntance.
        if action == 'list':
            self.view = subview(self.list_view_cls)
        elif action == 'new':
            self.view = subview(self.create_view_cls)
        else:
            pk = action
            self.object = self.get_object(pk)

            if not args:
                self.view = subview(self.detail_view_cls)
            elif args[0] == 'edit':
                args = args[1:]
                self.args = args
                self.view = subview(self.edit_view_cls)
            else:
                action, *args = args
                self.args = args
                self.view = subview(self.action_view_cls, action=action)

        return self.view.dispatch(request, *args, **kwargs)

    def subview_factory(self, cls, **kwargs):
        """
        Creates a new view instance from the given class and init arguments.
        """

        view = cls(**kwargs)
        view.manager = self
        if hasattr(view, 'get') and not hasattr(view, 'head'):
            view.head = view.get
        return view


class MultiViewTypeDispatcher(MultiViews):
    def __init__(self, object=None, **kwds):
        if type(self) is MultiViewTypeDispatcher:
            raise RuntimeError('This is an abstract class: can only create '
                               'instances of subtypes')
        self.object = None
        self.initkwargs = kwds

    abstract = True

    @property
    def edit_view_cls(self):
        return self.registry[type(self.object)].edit_view_cls

    @property
    def detail_view_cls(self):
        return self.registry[type(self.object)].detail_view_cls

    @property
    def action_view_cls(self):
        return self.registry[type(self.object)].action_view_cls

    @property
    def create_view_cls(self):
        suffix = self.args[0]
        self.args = self.args[1:]
        return self.registry[suffix].create_view_cls

    @classmethod
    def register(cls, *args):
        """
        Register a MultiView class associated with some model.
        """

        if len(args) == 1:
            def decorator(decorated):
                cls.register(decorated, args[0])
                return decorated
            return decorator
        subview, suffix = args

        if subview.model is None:
            raise TypeError('subview class must define a .model attribute.')

        if not hasattr(cls, 'registry'):
            cls.registry = {}
        cls.registry[subview.model] = subview
        cls.registry[suffix] = subview
        subview.parent_cls = cls

    def get_object(self, *args):
        """
        Return an object from the given reference arguments.

        Usually they correspond to a single pk argument or a slug field.
        """

        return self.model.objects.get_subclass(pk=args[0])

    def subview_factory(self, cls, **kwargs):
        view = super().subview_factory(cls, **kwargs)
        view.manager = manager = cls.manager_cls(**self.initkwargs)
        manager.parent = self
        manager.object = self.object
        return view


class DetailObject:
    """
    Exposes object with a normalized interface that can be conveniently
    used in generic templates.
    """

    def __init__(self, manager):
        self._manager = manager

    def __getattr__(self, attr):
        return getattr(self.object, attr)

    @lazy
    def object(self):
        return self._manager.object

    @lazy
    def title(self):
        try:
            return self.object.title
        except AttributeError:
            return self.object.name

    @lazy
    def short_description(self):
        try:
            return self.object.short_description
        except AttributeError:
            if hasattr(self.object, 'long_description'):
                return getattr(self.object, 'description', None)

    @lazy
    def long_description(self):
        try:
            return self.object.long_description
        except AttributeError:
            return getattr(self.object, 'description', None)

    @lazy
    def details(self):
        # Get field names
        manager_cls = type(self._manager)
        ns = manager_cls.get_field_definition_namespace((manager_cls,))
        fields = ns['fields']

        # Return list with field values
        out = []
        obj = self.object
        blacklist = {'title', 'name', 'short_description', 'long_description'}

        for field in fields:
            if field not in blacklist:
                data = getattr(obj, field, None)
                field = obj._meta.get_field(field)
                label = str(field.verbose_name).title()
                out.append((label, data))

        return out


class LazyBool:
    """
    Lazy boolean-like value.
    """

    def __init__(self, callable):
        self.callable = callable

    @lazy
    def value(self):
        return self.callable()

    def __bool__(self):
        return bool(self.value)

    def __add__(self, other):
        return self.value.__add__(other)

    def __radd__(self, other):
        return self.value.__radd__(other)

    def __sub__(self, other):
        return self.value.__sub__(other)

    def __rsub__(self, other):
        return self.value.__rsub__(other)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)