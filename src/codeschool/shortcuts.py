#
# Drop-in replacement to django.shortcuts.
#
# It adds some useful 3rd party functions that can be used in all codeschool
# modules. It also implement a few codeschool-specific shortcuts.
#


from functools import singledispatch
from django.shortcuts import *
from django.contrib.auth.context_processors import PermWrapper as _PermWrapper
from django.contrib.staticfiles.storage import (staticfiles_storage as
                                                _staticfiles_storage)
from django.template.response import TemplateResponse as _TemplateResponse
from annoying.functions import (get_object_or_None, get_object_or_this,
                                get_config)
from codeschool.utils import *
render_registry = {}


def render_context(request, template, context=None, **kwds):
    """
    Render page using the given template, request and namespace.

    Additional keywords are appended to the namespace
    """

    if context is not None:
        kwds = dict(context, **kwds)

    if request is not None:
        user = kwds['user'] = getattr(request, 'user', None)
        kwds['perms'] = _PermWrapper(user)
    return render(request, template, kwds)


def render_context_to_string(request, template, context=None, **kwds):
    """
    Similar to render_context, but return a string instead of an HttpResponse
    object.
    """

    if context is not None:
        kwds = dict(context, **kwds)

    if request is not None:
        user = kwds['user'] = getattr(request, 'user', None)
        kwds['perms'] = _PermWrapper(user)
    response = _TemplateResponse(request, template, kwds)
    return response.render()


def get_static_url(url):
    """
    Return the expanded url of an static files.

    On most configurations this simply prepends /static/ to the given url.
    """

    return _staticfiles_storage.url(url)


def populate(cls):
    """
    Register a signal handler that make class call its populate() classmethod
    just after it has been prepared.

    Users must be careful to implement populate() in a way that is safe if the
    method is called several times during the application lifecycle.
    """

    from django.db import models

    def handler(sender, **kwds):
        cls.populate()

    models.signals.class_prepared.connect(handler)
    return cls


@singledispatch
def render_html(object, template_name=None, context=None, object_context_name=None):
    """Renders object with the template with the given template name.

    A context with additional variables can be given. By default, it renders
    the template with a context that contains the passed `object`, which is
    saved both in a context variable named object "object" and in variable named
    with the value of `object_context_name`.

    If not given, `object_context_name`  assumes the value of the object's type
    in lowercase.

    This function accepts single argument dispatch and can be overridden to
    specific types using::

        @render_object.register(FooType)
        def _(object, template_name=None, context=None, **kwargs):
            template_name = 'render/foo_template.jinja2'

            # compute something that is pertinent to foo objects
            context = {...}

            # You can save the object in the context and pass None as the object
            # in order to simulate a super() call
            context['object'] = object
            return render_object(None, template_name, context, **kwargs)

    It is not necessary to override the render function just set a default
    template_name value. Just use the register_template function::

        register_template(FooModel, 'render/foomodel_template.jinja2')
    """

    context = dict(context or ())
    context['object'] = object
    return render_none(None, template_name, context, object_context_name)


@render_html.register(type(None))
def render_none(object, template_name=None, context=None,
                object_context_name=None):
    """
    Super-like end point for generic render implementations.
    """

    # Prepare context
    context = dict(context or ())
    object_context = context.setdefault('object', object)
    if object is None:
        object = object_context

    # Prepare object_context_name
    if object_context_name is None:
        object_context_name = type(object).__name__.lower()
    object_context_name = context.setdefault(object_context_name, object)

    # Choose template and render
    if template_name is None:
        template_name = render_registry.get(
            type(object), [
                'render/%s_template.jinja2' % object_context_name,
                'render/default.jinja2'
            ])
    return loader.render_to_string(template_name, context=context)


def register_template(cls, template_name):
    """
    Register the default template name for the given type.
    """

    if render_registry.get(cls, template_name) != template_name:
        raise ValueError('cannot register %s type twice.' % cls.__name__)
    render_registry[cls] = template_name


render_html.register_template = register_template