from django.views.generic import detail
from viewpack.views.utils import check_mro
from viewpack.utils import lazy, delegate_to_parent
from viewpack.views.permission import CanViewMixin
from viewpack.views.base import (
    ChildViewMixin,
    ContextMixin,
    TemplateResponseMixin
)


@check_mro
class SingleObjectMixin(ContextMixin, detail.SingleObjectMixin):
    """
    Provides the ability to retrieve a single object for further manipulation.
    """

    model = delegate_to_parent('model')
    queryset = delegate_to_parent('queryset')
    slug_field = delegate_to_parent('slug', 'slug')
    context_object_name = delegate_to_parent('context_object_name')
    slug_url_kwarg = delegate_to_parent('slug_url_kwarg', 'slug')
    pk_url_kwarg = delegate_to_parent('pk_url_kwarg', 'pk')
    query_pk_and_slug = delegate_to_parent('query_pk_and_slug', False)

    def get_object(self, queryset=None):
        if 'object' in self.__dict__:
            return self.object
        try:
            return self.parent.get_object(queryset)
        except (AttributeError, NotImplementedError):
            return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.object:
            obj = self.object
            for parent in self.parents:
                name = getattr(parent, 'object_context_name', None)
                if name is None:
                    name = parent.model.__name__.lower()
                context.setdefault(name, obj)

        return context


@check_mro
class SingleObjectTemplateResponseMixin(
        TemplateResponseMixin,
        detail.SingleObjectTemplateResponseMixin):

    # template_name_suffix = '_detail'
    template_name_field = delegate_to_parent('template_name_field')

    def get_template_names(self):
        # We mostly copy Django's implementation but insert the given template
        # extension instead of the hard-coded .html
        try:
            names = super().get_template_names()
        except ImproperlyConfigured:
            names = []
            extension = self.template_extension
            extension = '.' + extension.lstrip('.') if extension else extension

            if self.object and self.template_name_field:
                name = getattr(self.object, self.template_name_field, None)
                if name:
                    names.insert(0, name)

            if isinstance(self.object, models.Model):
                object_meta = self.object._meta
                if self.object._deferred:
                    object_meta = self.object._meta.proxy_for_model._meta
                names.append("%s/%s%s%s" % (
                    object_meta.app_label,
                    object_meta.model_name,
                    self.template_name_suffix,
                    extension,
                ))
            elif hasattr(self,
                         'model') and self.model is not None and issubclass(
                    self.model, models.Model):
                names.append("%s/%s%s%s" % (
                    self.model._meta.app_label,
                    self.model._meta.model_name,
                    self.template_name_suffix,
                    extension
                ))

            if not names:
                raise

        names.extend(self.get_parent_template_names())
        return names


@check_mro
class DetailView(CanViewMixin,
                 SingleObjectTemplateResponseMixin,
                 SingleObjectMixin,
                 detail.DetailView):
    """
    Render a "detail" view of an object.

    By default this is a model instance looked up from `self.queryset`, but the
    view will support display of *any* object by overriding `self.get_object()`.

    It looks up all attributes related to the detail view in the parent object,
    if not defined in the view class.
    """

    check_permissions = delegate_to_parent('check_permissions', False)
    raise_404_on_permission_error = delegate_to_parent('check_permissions', True)

