from django.db.models.fields import NOT_PROVIDED
from django import http
from codeschool.models import User
from codeschool.shortcuts import render_context, render, redirect
from codeschool.decorators import login_required
from cs_activities.models import Activity
from cs_questions import models
from cs_questions.forms import ImportQuestionForm

users = User.objects
type_map = {}


def register_question_type(tt, name, cls=None, *, detail=None, new=None, **kwds):
    """
    Register question type.
    """

    def make_action(name):
        def action_func(request, obj, *args, **kwds):
            manager = cls()
            method = login_required(getattr(manager, 'view_' + name))
            return method(request, obj, *args, **kwds)
        return action_func

    if cls:
        for action in dir(cls):
            if not action.startswith('view_'):
                continue

            action = action[5:]
            if action == 'new' and not new:
                new = lambda r: login_required(cls().view_new)(r)
            elif action == 'detail' and not detail:
                detail = lambda r, o: login_required(cls().view_detail)(r, o)
            else:
                kwds[action.replace('_', '-')] = make_action(action)

    kwds.update(new=new, view=detail)
    kwds = {k: v for (k, v) in kwds.items() if v is not None}
    type_map[tt] = kwds
    type_map[name] = kwds


def index(request):
    """List of all public questions."""

    return render_context(
        request,
        'cs_questions/index.jinja2',
        questions=models.Question.objects.all().order_by('pk')
    )


def question_detail(request, pk):
    """Generic view that dispatch to the detail page for a given question."""

    try:
        obj = models.Question.objects.get_subclass(pk=pk)
    except models.Question.DoesNotExist:
        raise http.Http404

    try:
        method = type_map[type(obj)]['view']
    except KeyError:
        raise http.Http404
    return method(request, obj)


def question_action(request, pk, action):
    """Generic view that dispatch question actions."""

    action, *args = action.split('/')
    try:
        obj = models.Question.objects.get_subclass(pk=pk)
    except models.Question.DoesNotExist:
        raise http.Http404('no question with pk=%s found.' % pk)

    try:
        method = type_map[type(obj)][action]
    except KeyError:
        raise http.Http404
    return method(request, obj, *args)


def question_new(request, type_name):
    """Dispatch to a page for creating new questions."""

    try:
        method = type_map[type_name]['new']
    except KeyError:
        raise http.Http404
    return method(request)


# Basic question types
class QuestionViews:
    """
    Base class that implements generic behaviour for question-related views.

    The methods named as view_<action> correspond each action that is
    pertinent to some given question object. All these methods receive at least
    a request and a question object as positional arguments. Additional
    arguments might appear in more nested urls::

        http://.../questions/<question_pk>/<action>/<arg1>/<arg2>/...

    """
    name = 'generic'
    model = models.Question
    import_form = ImportQuestionForm
    exclude_fields = ('owner', 'comment', 'author_name')
    exclude_response_fields = ()
    __form_models_map = {}

    @property
    def model_form(self):
        """Stores the FormModel for the given model."""

        try:
            return self.__form_models_map[self.model]
        except KeyError:
            from django import forms

            class ModelForm(forms.ModelForm):
                class Meta:
                    model = self.model
                    fields = self._model_fields()

            self.__form_models_map[self.model] = ModelForm
            return ModelForm

    @property
    def response_form(self):
        """Form for user responses"""

        try:
            return self.__form_models_map[self.model.response_cls]
        except KeyError:
            from django import forms

            class ModelForm(forms.ModelForm):
                class Meta:
                    model = self.model.response_cls
                    fields = self._response_fields()
                    print(fields)

            self.__form_models_map[self.model.response_cls] = ModelForm
            return ModelForm

    def _model_fields(self):
        """Return a list of model fields to create the ModelForm"""

        fields = [x.name for x in self.model._meta.concrete_fields]

        # Remove undesired and system-created fields
        exclude = ('id', 'question_ptr', 'modified', 'created')
        exclude += tuple(self.exclude_fields)
        for f in exclude:
            fields.remove(f)

        return fields

    def _response_fields(self):
        """Return a list of response fields to create the response ModelForm"""

        model = self.model.response_cls
        fields = [x.name for x in model._meta.concrete_fields]

        # Remove undesired and system-created fields
        exclude = ('id', 'created', 'modified', 'status', 'status_changed',
                   'activity', 'group', 'user', 'response_ptr')
        exclude += tuple(self.exclude_response_fields)

        for f in exclude:
            fields.remove(f)

        return fields

    def _fsetdefault(self, D, key, callable):
        """If mapping D no not has key, sets its content to the result of
        callable."""

        if key not in D:
            D[key] = callable()

    def render(self, request, template, context):
        """Renders request using the template given by

            'cs_questions/<name>/<template>.jinja2'

        Name is usually defined as a class variable such as 'io' for
        CodingIoQuestions, 'numeric' for NumericQuestions and so forth.
        """

        name = 'cs_questions/%s/%s.jinja2' % (self.name, template)
        return render(request, name, context)

    def fill_default_values(self, question):
        """Fill all empty default values from the question object."""

        for f in question._meta.fields:
            if f.default != NOT_PROVIDED:
                value = getattr(question, f.name)
                if value is None:
                    value = f.default() if callable(f.default) else f.default
                    setattr(question, f.name, value)

    def copy_data_from(self, new, old):
        """Copy data from old question instance to the new question instance.

        It is necessary to override this method in order to support copying
        questions with many-to-many relationship."""

    def import_question(self, data, context):
        """Import question from the given string of data.

        The context dictionary can be modified by this function to include error
        messages in the 'import_error' variable. If import is successful,
        'import_ok' should also be set to True and the method should return the
        equivalent question object.
        """

        raise NotImplementedError

    # Generic views
    def view_new(self, request, extra_context=None):
        """Creates a new question."""

        context = {}

        if request.FILES:
            data = request.FILES['file'].read().decode('utf8')
            question = self.import_question(data, context)
            if question is not None:
                context['form'] = self.model_form(instance=question)

        elif request.method == 'POST':
            context['form'] = form = self.model_form(request.POST)

            if form.is_valid():
                question = form.save(commit=False)
                question.owner = request.user
                self.fill_default_values(question)
                question = form.save()
                return redirect('../../%s/edit' % question.pk)

        self._fsetdefault(context, 'form', self.model_form)
        self._fsetdefault(context, 'import_form', self.import_form)
        context.update(extra_context or {})
        return self.render(request, 'edit', context)

    def view_edit(self, request, question, extra_context=None):
        """Edit the given question object."""

        if not question.can_edit(request.user):
            raise http.Http404

        if request.method == 'POST':
            form = self.model_form(request.POST, instance=question)

            if form.is_valid():
                action = request.POST.get('action', None)

                if action == 'delete':
                    question.delete()
                    return redirect('/questions/')
                elif action == 'copy':
                    form = self.model_form(request.POST)
                    new = form.save()
                    self.copy_data_from(new, question)
                    new.owner = request.user
                    new.update()
                    return redirect('../../%s/edit' % new.pk)
                elif action == 'view':
                    form.save().update()
                    return redirect('../')
                else:
                    form.save().update()
        else:
            form = self.model_form(instance=question)

        context = {'question': question, 'form': form}
        context.update(extra_context or {})

        return self.render(request, 'edit', context)

    def view_detail(self, request, question, extra_context=None):
        """The details page for question: it shows description and a form for
        the user to submit its responses.

        This method that the class attribute response_form should hold a django
        form class that processes form inputs."""

        context = {
            'grade': None,
            'feedback': None,
            'question': question,
            'can_download': question.can_edit(request.user),
        }

        if request.method == 'GET':
            if 'activity' in request.GET:
                context['activity'] = request.GET['activity']
            else:
                context['activity'] = None

        elif request.method == 'POST':
            # Should we associate an activity to the response?
            activity = None
            try:
                activity = request.POST['activity']
                activity = Activity.objects.get_subclass(pk=activity)
            except KeyError:
                pass
            context['activity'] = activity

            # Get response
            form = self.response_form(request.POST)
            if form.is_valid():
                response = form.save(commit=False)
                response.user = request.user
                response.activity = activity
                response.save()

                # Grade it and save feedback
                feedback = question.grade(response)
                feedback.save()
                context['grade'] = int(feedback.grade * 100)
                context['feedback'] = feedback

        context.update(extra_context or {})
        self._fsetdefault(context, 'form', self.response_form)
        return self.render(request, 'detail', context)

    def view_download(self, request, question, ext=None):
        """Download question in an specialized format."""

        if not question.can_edit(request.user):
            raise http.Http404

        data = question.export(ext)
        if data is NotImplemented:
            raise http.Http404

        ext = (ext or question.default_extension).lstrip('.')
        filename = '%s.%s' % (question.title, ext)
        content_type = {
            'md': 'application/markdown',
            'json': 'application/json'
        }[ext]
        response = http.HttpResponse(data, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename = %s' % filename
        return response


class NumericQuestionViews(QuestionViews):
    name = 'numeric'
    model = models.NumericQuestion

    def import_question(self, data, context):
        #TODO: define format to multiple choice questions
        raise NotImplementedError


# Register default question types
def register_default():
    from cs_questions.question_coding_io.views import CodingIoQuestionViews
    register_question_type(models.io.CodingIoQuestion, 'io', CodingIoQuestionViews)
    register_question_type(models.NumericQuestion, 'numeric', NumericQuestionViews)

register_default()


