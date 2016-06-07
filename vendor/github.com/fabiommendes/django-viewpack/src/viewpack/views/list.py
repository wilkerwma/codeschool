from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.views.generic import list as list_
from viewpack.views.utils import check_mro
from viewpack.utils import lazy, delegate_to_parent
from viewpack.views.base import ContextMixin, TemplateResponseMixin


@check_mro
class MultipleObjectMixin(ContextMixin, list_.MultipleObjectMixin):
    """
    A mixin for views manipulating multiple objects.
    """

    allow_empty = delegate_to_parent('allow_empty', True)
    queryset = delegate_to_parent('queryset')
    model = delegate_to_parent('model')
    paginate_by = delegate_to_parent('paginate_by')
    paginate_orphans = delegate_to_parent('paginate_orphans', 0)
    context_object_name = delegate_to_parent('context_object_name')
    paginator_class = delegate_to_parent('paginator_class', Paginator)
    page_kwarg = delegate_to_parent('page_kwarg', 'page')
    ordering = delegate_to_parent('ordering')


@check_mro
class MultipleObjectTemplateResponseMixin(
        TemplateResponseMixin,
        list_.MultipleObjectTemplateResponseMixin):

    """
    Mixin for responding with a template and list of objects.
    """

    def get_template_names(self):
        try:
            names = super().get_template_names()
        except ImproperlyConfigured:
            names = []

        if hasattr(self.object_list, 'model'):
            opts = self.object_list.model._meta

            # This is almost exactly the the default django implementation. We
            # just change the lines bellow in order to support different
            # extensions.
            extension = self.template_extension
            extension = '.' + extension.lstrip('.') if extension else extension
            names.append("%s/%s%s%s" % (
                opts.app_label,
                opts.model_name,
                self.template_name_suffix,
                extension
            ))

        names.extend(self.get_parent_template_names())
        return names


@check_mro
class ListView(MultipleObjectTemplateResponseMixin, MultipleObjectMixin,
               list_.ListView):
    """
    Render some list of objects, set by `self.model` or `self.queryset`.
    `self.queryset` can actually be any iterable of items, not just a queryset.
    """
