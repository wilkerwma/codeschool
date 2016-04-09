#
# Drop-in replacement to django.shortcuts.
#
# It adds some useful 3rd party functions that can be used in all codeschool
# modules. It also implement a few codeschool-specific shortcuts.
#


from django.shortcuts import *
from django.contrib.auth.context_processors import PermWrapper as _PermWrapper
from django.contrib.staticfiles.storage import (staticfiles_storage as
                                                _staticfiles_storage)
from django.template.response import TemplateResponse as _TemplateResponse
from annoying.functions import (get_object_or_None, get_object_or_this,
                                get_config)
from codeschool.utils import *


def render_context(request, template, **kwds):
    """Render page using the given template, request and namespace.

    Additional keywords are appended to the namespace"""

    if request is not None:
        user = kwds['user'] = getattr(request, 'user', None)
        kwds['perms'] = _PermWrapper(user)
    return render(request, template, kwds)


def render_context_to_string(request, template, **kwds):
    """Similar to render_context, but return a string instead of an HttpResponse
    object."""

    if request is not None:
        user = kwds['user'] = getattr(request, 'user', None)
        kwds['perms'] = _PermWrapper(user)
    response = _TemplateResponse(request, template, kwds)
    return response.render()


def get_static_url(url):
    """Return the expanded url of an static files.

    On most configurations this simply prepends /static/ to the given url"""

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