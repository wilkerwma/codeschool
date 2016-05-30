from django.forms import Form, FileField
from django.forms.models import modelform_factory
from viewpack.utils import lazy, delegate_to_parent
from viewpack.types import DetailObject, LazyBool
from viewpack.views.base import View
from viewpack.views.edit import FormMixin
from viewpack.views.detail import DetailView


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


class UploadForm(Form):
    file = FileField()


class HasUploadMixin:
    """Adds support for upload an serialized version of object from the create
    view. Respond to multi-part POST requests and import the uploaded file into
    a new object.

    Context attributes:
        upload_enable:
            Enable upload functionality.
        upload_form:
            A form instance for the upload form.
        upload_ask:
            True if needs to ask for upload, False otherwise (for displaying
            success/failure messages).
        upload_error:
            A message with the upload error, if it exists.
    """

    #: Enable the upload functionality (default True)
    upload_enable = delegate_to_parent('upload_enable', True)

    #: Default upload form class
    upload_form_class = UploadForm

    #: The exception class raised on import errors
    import_object_exception = delegate_to_parent('import_object_exception',
                                                 SyntaxError)

    #: The url to redirect upon success. It accepts the format syntax in which
    #: is called with a dictionary with {'object': imported_object}
    upload_success_url = delegate_to_parent('upload_success_url')

    def get_context_data(self, **kwargs):
        if self.upload_enable:
            return super().get_context_data(
                upload_form=self.get_upload_form(),
                upload_ask=getattr(self, 'upload_ask', True),
                upload_error=getattr(self, 'upload_error', None),
                upload_enable=True,
                **kwargs
            )
        else:
            return super().get_context_data(upload_enable=False, **kwargs)

    def get_upload_form(self, *args, **kwargs):
        """Return a Form instance representing an upload form."""

        cls = self.get_upload_form_class()
        return cls(*args, **kwargs)

    def get_upload_form_class(self):
        """Return the Form subclass used from upload forms."""

        return self.upload_form_class

    def post(self, request, *args, **kwargs):
        if self.upload_enable and request.FILES:
            form = self.get_upload_form(request.POST, request.FILES)
            if form.is_valid():
                try:
                    self.object = self.get_object_from_files(request.FILES)
                except self.import_object_exception as ex:
                    self.upload_error = str(ex) or 'import error'
                    return self.upload_failure(request, *args, **kwargs)
                else:
                    return self.upload_success(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def upload_success(self, request, *args, **kwargs):
        """Called when import is successful."""

        if self.upload_success_url is None:
            if hasattr(self.object, 'get_absolute_url'):
                url = self.object.get_absolute_url()
            else:
                raise ImproperlyConfigured(
                    'You must either override the upload_success() method or '
                    'define a `upload_success_url` attribute.'
                )
        else:
            url = self.upload_success_url.format(object=self.object)
        return redirect(url)

    def upload_failure(self, request, *args, **kwargs):
        """Called when import failed."""

        self.upload_ask = False
        return self.get(request, *args, **kwargs)

    def get_object_from_files(self, files):
        """Return object from the dictionary of files uploaded by the user.

        By default it expects a dictionary with a single 'file' key. This
        function reads this file and calls the `get_object_from_data()` method.
        """

        data = files['file'].read()
        obj = self.get_object_from_data(data)
        set_owner = getattr(self.parent, 'set_owner', lambda x, u: None)
        set_owner(obj, self.request.user)
        return obj

    def get_object_from_data(self, data):
        """Returns a new instance from data sent by the user.

        Object is always saved on the database."""

        obj = self.model.from_data(data)
        if obj.pk is None:
            obj.save()
        return obj