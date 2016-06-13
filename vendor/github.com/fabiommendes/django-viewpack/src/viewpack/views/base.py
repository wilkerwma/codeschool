from django.core.exceptions import ImproperlyConfigured
from django.views.generic import base
from django.template.response import TemplateResponse
from viewpack.views.utils import check_mro
from viewpack.utils import lazy, delegate_to_parent, get_view_name


class ChildViewMixin:
    """
    Implements functionality in the base :class:`viewpack.views.View`.
    """
    parent = None
    pattern = None
    view_name = None
    url_name = None

    @lazy
    def parents(self):
        """A list with all parents to the given view."""

        chain = []
        parent = self.parent

        while parent is not None:
            if parent in chain:
                raise RuntimeError('recursive parent hierarchy')
            chain.append(parent)
            parent = parent.parent
        return chain

    def iter_parents(self):
        """Iterate over all parents, including itself as first element."""

        yield self
        for parent in self.parents:
            yield parent

    def __getattr__(self, attr):
        if self.parent is None:
            raise AttributeError('%s instance has no attribute %r' %
                                 (type(self).__name__, attr))
        return getattr(self.parent, attr)


@check_mro
class View(ChildViewMixin, base.View):
    """
    Base mixin class that is applied to all child views.

    This mixin defines some extra attributes and make it seach for any
    undefined attributes in the parent view pack.

    Attributes:
        parent:
            The parent view pack for this view. This is defined during the
            initialization of a ChildView object.
        pattern:
            A string with a regular expression matching the url pattern
            associated with this view. The default url is a dash-case version
            of the class name.
        view_name:
            A string with the name for this view. This name should be unique
            inside a view pack. By default, it is a dash-case version of the
            class name stripped of any trailing "-view" string.
        url_name:
            The name used to register this view in the django's reverse url
            mechanism. This defaults to the view_name attribute.
    """


class ParentContextMixin:
    """
    Calls parent's get_context_data, if exists, and prepends it to the context.
    """

    def get_context_data(self, **kwargs):
        if self.parent is not None:
            if hasattr(self.parent, 'context_data'):
                kwargs.update(self.parent.context_data)
            if hasattr(self.parent, 'get_context_data'):
                kwargs = self.parent.get_context_data(**kwargs)
        return super().get_context_data(**kwargs)


@check_mro
class ContextMixin(ChildViewMixin, ParentContextMixin, base.ContextMixin):
    """
    A default context mixin that passes the keyword arguments received by
    get_context_data as the template context.

    Differently from Django's builtin version, this view queries the parent's
    object `get_context_data` and add any context variables defined there. The
    view variables  always take precedence over the values defined in the parent
    object.
    """


class TemplateResponseEndpointMixin:
    """
    End point of TemplateView's MRO.
    """

    def get_template_names(self):
        return self.get_endpoint_template_names()

    def get_endpoint_template_names(self):
        """
        Execute the mro endpoint get_template_names method at
        TemplateResponseMixin
        """
        return base.TemplateResponseMixin.get_template_names(self)


class ParentTemplateNamesMixin:
    """
    A mixin that searches the parent object for extra template names.
    """
    def get_template_names(self):
        """
        Return a list of template names.

        It computes the list of template lists normally and then append the
        parent templates.
        """

        # We get both parent and super() templates. The first always have
        # precedence, but we append any parent template to the list if they are
        # present
        parent_templates = self.get_parent_template_names()
        try:
            templates = super().get_template_names()
        except ImproperlyConfigured:
            if parent_templates:
                return parent_templates
            raise
        parent_templates = [x for x in parent_templates if x not in templates]
        templates.extend(parent_templates)
        return templates

    def get_parent_template_names(self):
        """
        Return a list of template names from parent object.

        If parent has no templates, or parent is not set, an empty list is
        returned
        """

        try:
            method = self.parent.get_template_names
        except AttributeError:
            return []
        else:
            return method(get_view_name(self))


@check_mro
class TemplateResponseMixin(ChildViewMixin,
                            ParentTemplateNamesMixin,
                            TemplateResponseEndpointMixin,
                            base.TemplateResponseMixin):
    """
    A mixin that can be used to render a template.
    """

    # template_name = None
    template_engine = delegate_to_parent('template_engine')
    response_class = delegate_to_parent('response_class', TemplateResponse)
    template_extension = delegate_to_parent('template_extension', '.html')
    content_type = delegate_to_parent('content_type')


@check_mro
class TemplateView(TemplateResponseMixin,
                   ContextMixin,
                   base.TemplateView):
    """
    A view that renders a template.  This view will also pass into the context
    any keyword arguments passed by the URLconf.

    It searches the parent object for additional template names by calling its
    `get_template_names(<view name>)` with the view_name for the current view.
    The templates returned by the parent object are appended to the currently
    defined template list and thus have a lower priority than any template name
    defined in the view.

    It understands the default attributes "template_engine", "response_class",
    and "content_type" as in the Django implementation. It also defines a new
    attribute "template_extension" that is used to specify the extension used
    for templates.

    If any of these attributes is **not** defined in the view, it tries to use
    the values defined in the parent object before raising a
    :error:`django.exceptions.ImproperlyConfigured` error.
    """


@check_mro
class RedirectView(ChildViewMixin, base.RedirectView):
    """
    A view that provides a redirect on any GET request.
    """

    permanent = False
    url = None
    pattern_name = None
    query_string = False
