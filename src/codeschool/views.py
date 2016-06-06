from functools import singledispatch
from django.core.urlresolvers import reverse
from django.template import loader
from codeschool.models import AnonymousUser
from codeschool.shortcuts import redirect
render_registry = {}


def index(request):
    """
    Codeschool index page.
    """
    # It redirects to the login page or to the profile page. It should probably
    # do something more interesting in the future.

    if isinstance(request.user, AnonymousUser):
        return redirect(reverse('auth:login'))
    else:
        return redirect('/courses/')


@singledispatch
def render_object(object, template_name=None, context=None, object_context_name=None):
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


@render_object.register(type(None))
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
