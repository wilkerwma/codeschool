from django.core.exceptions import ImproperlyConfigured
from viewpack.utils import lazy, delegate_to_parent
from viewpack.views.mixins import SingleObjectMixin, TemplateResponseMixin


class SingleObjectPackMixin(SingleObjectMixin):
    """
    A parent view pack that exposes different urls that can control a single
    object.
    """

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


class TemplateResponsePackMixin(TemplateResponseMixin):
    """
    Add <template_basename><sub-view name>.<template_extension> to the list of
    templates.

    <sub-view name> is the name of the child view that is going to process the
    current request.

    This method only work if the child views inherit from the classes in
    :mod:`viewpack.views`. Theses classes inherit from Django built-in classes,
    and have the same API, but they insert hooks to search for some default
    values in the parent classes.
    """

    template_basename = delegate_to_parent('template_basename')
    template_extension = delegate_to_parent('template_extension', '.html')

    @lazy
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
