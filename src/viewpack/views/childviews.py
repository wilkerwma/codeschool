from django.views.generic import (base, edit, detail, list as list_, dates,
                                  GenericViewError)
from django.forms.models import modelform_factory
from django.template.response import TemplateResponse
from django.core.paginator import Paginator
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django import http
from viewpack.utils import lazy, delegate_to_parent, get_view_name
from viewpack.types import DetailObject, LazyBool

__all__ = [
    # Base
    'View', 'TemplateView', 'RedirectView',

    # Dates
    'ArchiveIndexView', 'YearArchiveView', 'MonthArchiveView',
    'WeekArchiveView', 'DayArchiveView', 'TodayArchiveView', 'DateDetailView',

    # Detail
    'DetailView',

    # Edit
    'FormView', 'CreateView', 'UpdateView', 'DeleteView',

    # List
    'ListView',

    # Extra
    'FormActionsView', 'Http404View', 'DetailWithResponseView',

    # Error
    'GenericViewError',
]


#
# Check if all methods have the correct MRO
#
CHECK_MRO = True
MRO_NEUTRAL = {
    'ParentTemplateNamesMixin.get_template_names',
    'ParentContextMixin.get_context_data',
    'SingleObjectMixin.get_context_data',
}
MRO_STOP = {
    'TemplateResponseEndpointMixin.get_template_names':
        '*TemplateResponseMixin.get_template_names'
}


def mmro(cls, method):
    """
    Return a list of strings with the MRO for the given method in the class.
    """

    result = []
    for subclass in cls.mro():
        if method in subclass.__dict__:
            mark = '' if 'viewpack' in subclass.__module__ else '*'
            result.append('%s%s.%s' % (mark, subclass.__name__, method))
    return result


def check_mro(cls=None, *, ommit=()):
    """Checks if class define the correct MRO for all public method."""

    if cls is None:
        def decorator(cls):
            return check_mro(cls, ommit=ommit)

        return decorator

    if not CHECK_MRO:
        return cls

    # We assume that each class represents a re-implementation of its last base,
    # which should have the same class name
    original = cls.__bases__[-1]
    if cls.__name__ != original.__name__:
        raise ValueError('Should inherit from %s, got %s' %
                         (cls.__name__, original.__name__))

    # Now we check the mro of each public method. We expect that the derived
    # mro begins the same as the original one.
    for method in dir(cls):
        if method.startswith('_') or method in ommit:
            continue

        # Skip properties and constants
        value = getattr(cls, method)
        if isinstance(value, (property, lazy)):
            continue

        mro = mmro(cls, method)
        mro_original = mmro(original, method)
        mro_ = list(mro)
        mro_original_ = list(mro_original)

        # Remove neutral methods from both mro's. We break the mro in any
        # registered MRO_STOP method
        for L in [mro_, mro_original_]:
            for i, method in enumerate(L):
                if method in MRO_STOP:
                    L[i] = MRO_STOP[method]
                    L[:] = L[:i + 1]
                    break
            L[:] = [x.replace('*', '') for x in L if x not in MRO_NEUTRAL]

        # Check if both mro's begin the same
        if not all(x == y for (x, y) in zip(mro_, mro_original_)):
            raise AssertionError(
                'Got an unexpected mro for %s:\n' % cls.__name__ +
                '    %s\n    %s\nas\n    %s\n    %s\n' % (
                    mro, mro_original, mro_, mro_original_
                )
            )

    return cls


#
# Private mixins and views
#
class TemplateResponseEndpointMixin:
    """
    End point of TemplateViews MRO
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


#
# Base mixins and views
#
class ChildViewMixin:
    """
    Base mixin class that is applied to all child views.
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
class ContextMixin(ChildViewMixin, ParentContextMixin, base.ContextMixin):
    pass


@check_mro
class View(ChildViewMixin, base.View):
    pass


@check_mro
class TemplateResponseMixin(ChildViewMixin,
                            ParentTemplateNamesMixin,
                            TemplateResponseEndpointMixin,
                            base.TemplateResponseMixin):
    # template_name = None
    template_engine = delegate_to_parent('template_engine')
    response_class = delegate_to_parent('response_class', TemplateResponse)
    template_extension = delegate_to_parent('template_extension', '.html')
    content_type = delegate_to_parent('content_type')


@check_mro
class TemplateView(TemplateResponseMixin,
                   ContextMixin,
                   base.TemplateView):
    pass


@check_mro
class RedirectView(ChildViewMixin, base.RedirectView):
    pass


#
# Detail mixins and views
#
@check_mro
class SingleObjectMixin(ContextMixin, detail.SingleObjectMixin):
    model = delegate_to_parent('model')
    queryset = delegate_to_parent('queryset')
    slug_field = delegate_to_parent('slug', 'slug')
    context_object_name = delegate_to_parent('context_object_name')
    slug_url_kwarg = delegate_to_parent('slug_url_kwarg', 'slug')
    pk_url_kwarg = delegate_to_parent('pk_url_kwarg', 'pk')
    query_pk_and_slug = delegate_to_parent('query_pk_and_slug', False)

    def get_object(self, queryset=None):
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
class SingleObjectTemplateResponseMixin(TemplateResponseMixin,
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
class DetailView(SingleObjectTemplateResponseMixin, SingleObjectMixin,
                 detail.DetailView):
    pass


#
# Edit mixins and views
#
@check_mro
class FormMixin(ChildViewMixin, edit.FormMixin):
    pass


@check_mro
class ModelFormMixin(FormMixin, SingleObjectMixin, edit.ModelFormMixin):
    fields = delegate_to_parent('fields')


@check_mro
class FormView(TemplateResponseMixin, edit.FormView):
    pass


@check_mro
class CreateView(SingleObjectTemplateResponseMixin, ModelFormMixin,
                 edit.CreateView):
    pass


@check_mro
class UpdateView(SingleObjectTemplateResponseMixin, ModelFormMixin,
                 edit.UpdateView):
    pass


@check_mro
class DeletionMixin(ChildViewMixin, edit.DeletionMixin):
    pass


@check_mro
class DeleteView(SingleObjectTemplateResponseMixin, SingleObjectMixin,
                 edit.DeleteView):
    pass


#
# List mixins and views
#
@check_mro
class MultipleObjectMixin(ContextMixin, list_.MultipleObjectMixin):
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
class MultipleObjectTemplateResponseMixin(TemplateResponseMixin,
                                          list_.MultipleObjectTemplateResponseMixin):
    def get_template_names(self):
        try:
            names = super().get_template_names()
        except ImproperlyConfigured:
            names = []

        if hasattr(self.object_list, 'model'):
            opts = self.object_list.model._meta

            # This is almost exactly the the default django implementation. We
            # just change the line bellow in order to support different extensions.
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
    pass


#
# Dates
#
@check_mro
class YearMixin(ChildViewMixin, dates.YearMixin):
    year_format = delegate_to_parent('year_format', '%Y')
    year = delegate_to_parent('year')


@check_mro
class MonthMixin(ChildViewMixin, dates.MonthMixin):
    month_format = delegate_to_parent('month_format', '%b')
    month = delegate_to_parent('month')


@check_mro
class DayMixin(ChildViewMixin, dates.DayMixin):
    day_format = delegate_to_parent('day_format', '%d')
    day = delegate_to_parent('day')


@check_mro
class WeekMixin(ChildViewMixin, dates.WeekMixin):
    week_format = delegate_to_parent('week_format', '%U')
    week = delegate_to_parent('week')


@check_mro
class DateMixin(ChildViewMixin, dates.DateMixin):
    date_field = delegate_to_parent('date_field')
    allow_future = delegate_to_parent('allow_future', False)


@check_mro
class ArchiveIndexView(MultipleObjectTemplateResponseMixin,
                       dates.ArchiveIndexView):
    allow_empty = delegate_to_parent('allow_empty', False)


@check_mro
class YearArchiveView(MultipleObjectTemplateResponseMixin,
                      dates.YearArchiveView):
    make_object_list = delegate_to_parent('make_object_list', False)


@check_mro
class MonthArchiveView(MultipleObjectTemplateResponseMixin,
                       dates.MonthArchiveView):
    pass


@check_mro
class WeekArchiveView(MultipleObjectTemplateResponseMixin,
                      dates.WeekArchiveView):
    pass


@check_mro
class DayArchiveView(MultipleObjectTemplateResponseMixin, dates.DayArchiveView):
    pass


@check_mro
class TodayArchiveView(MultipleObjectTemplateResponseMixin,
                       dates.TodayArchiveView):
    pass


@check_mro
class DateDetailView(SingleObjectTemplateResponseMixin, dates.DateDetailView):
    pass


#
# Extra views and mixins
#
class Http404View(View):
    """
    Raises a 404 error on any post or get requests.
    """

    def get(self, *args, **kwargs):
        raise http.Http404

    def post(self, *args, **kwargs):
        raise http.Http404


class FormActionsMixin:
    def form_valid(self, form):
        response = super().form_valid(form)
        action = self.request.POST.get('action')
        urlbase = self.request.get_full_path().rpartition('/new')[0]

        # if action == 'save':
        #    return redirect('%s/%s/edit' % (urlbase, self.object.pk))
        # return redirect('%s/%s/' % (urlbase, self.object.pk))


class FormActionsView(FormActionsMixin, FormMixin):
    pass


class VerboseNamesContextMixin:
    """
    Adds the model's verbose_name and verbose_name_plural to the context.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        meta = self.model._meta
        context.setdefault('verbose_name', meta.verbose_name)
        context.setdefault('verbose_name_plural', meta.verbose_name_plural)
        return context


class DetailObjectContextMixin:
    """
    Adds a DetailObject instance as the detail_object variable to the context.
    """

    def get_context_data(self, **kwargs):
        return super().get_context_data(detail_object=DetailObject(self),
                                        **kwargs)


class DetailWithResponseView(FormMixin, DetailView):
    """
    A detail view that creates a form to fill up a response object that
    represents the user interaction with that object in the detail view.

    One example is the user response to a quiz in the page that shows the quiz
    details.
    """

    response_form_class = delegate_to_parent('response_form_class')
    response_form_model = delegate_to_parent('response_form_model')
    response_fields = delegate_to_parent('response_fields')

    def post(self, request, *args, **kwargs):
        """
        Executed when response form is submitted.
        """

        form = self.get_form()
        if form.is_valid():
            self.response = self.get_response(form)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_class(self):
        """
        Return the form class for the response object to use in this view.
        """

        if self.response_model is not None and self.response_form_class:
            raise ImproperlyConfigured(
                "Specifying both 'response_model' and 'response_form_class' "
                "is not permitted."
            )
        if self.response_form_class:
            return self.response_form_class
        else:
            if not (self.response_model and self.response_fields):
                raise ImproperlyConfigured(
                    "Using DetailWithResponseView without the "
                    "'response_fields' and 'response_model' attributes is "
                    "prohibited."
                )

            model = self.response_model
            fields = self.response_fields
            return modelform_factory(model, fields=fields)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self, 'response'):
            kwargs.update({'instance': self.response})
        return kwargs

    def get_context_data(self, **kwargs):
        if 'response' not in kwargs:
            kwargs['response'] = getattr(self, 'response', None)
        return super().get_context_data(**kwargs)

    def get_response(self, form):
        """
        Create a response object from the given model form.

        This method is called after the form is validated. The default
        implementation simply calls the save() method of the ModelForm. It can
        be overridden in order to save or additional fields.
        """

        return form.save()
