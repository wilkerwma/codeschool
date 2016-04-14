import copy
from django import http
from codeschool.shortcuts import redirect, render
from cs_core.models import ProgrammingLanguage
from cs_questions.question_coding_io.forms import (
    QuestionEditForm,
    ImportQuestionForm,
    AnswerKeyEditForm,
    AnswerKeyAddForm,
)
from cs_questions.question_coding_io.models import (
    CodingIoQuestion,
    CodingIoActivity,
    CodingIoResponse
)


class QuestionViews:
    def new(self, request):
        #TODO: redirect to edit form ASAP
        context = {}
        import_form = ImportQuestionForm()
        form = QuestionEditForm(request.POST)
        question = None

        if request.FILES:
            data = request.FILES['file'].read().decode('utf8')
            try:
                question = CodingIoQuestion.from_markio(data)
                question.update(validate=True)
            except Exception as ex:
                ex = ex if isinstance(ex, SyntaxError) else ''
                context['import_ok'] = False
                context['import_error'] = 'This is not a valid Markio. ' + ex
            else:
                form = QuestionEditForm(instance=question)
                context['import_ok'] = question.status == question.STATUS_VALID
                context['import_error'] = question.status
                question.delete()

        elif request.method == 'POST':
            if form.is_valid():
                question = form.save(commit=False)
                question.owner = request.user
                for f in ['iospec_size', 'timeout']:
                    if getattr(question, f) is None:
                        data = question._meta.get_field(f).default
                        setattr(question, f, data)
                question = form.save()
                return redirect('../../%s/edit' % question.pk)

        context.update(form=form, import_form=import_form)
        return render(request, 'cs_questions/io/edit.jinja2', context)

    def detail(self, request, question):
        context = dict(grade=None, lang=None, feedback=None, question=question)
        context['languages'] = ProgrammingLanguage.objects.all()
        context['can_download'] = request.user == question.owner

        if request.method == 'GET':
            if 'activity' in request.GET:
                context['activity'] = request.GET['activity']

        elif request.method == 'POST':
            # Should we associate an activity to the response?
            activity = None
            try:
                activity = request.POST['activity']
                activity = CodingIoActivity.objects.get(pk=activity)
            except KeyError:
                pass

            # Fetch programming language
            lang = request.POST['lang']
            lang = ProgrammingLanguage.objects.get(ref=lang)

            # Construct response
            source_code = request.POST['source']
            response = CodingIoResponse(
                    user=request.user,
                    activity=activity,
                    source=source_code,
                    language=lang,
            )
            response.save()

            feedback = question.grade(response)
            feedback.save()
            context['selected_lang'] = lang.ref
            context['source_code'] = source_code
            context['grade'] = int(feedback.grade * 100)
            context['feedback'] = feedback

        return render(request, 'cs_questions/io/detail.jinja2', context)

    def edit(self, request, question, extra_context=None):
        if not question.can_edit(request.user):
            raise http.Http404
        used_langs = question.answer_keys.select_related('language')
        languages = ProgrammingLanguage.objects.exclude(pk__in=used_langs)
        context = {
            'question': question,
            'add_button': bool(languages),
            'show_answer_keys': True,
        }

        if request.method == 'POST':
            form = QuestionEditForm(request.POST, instance=question)

            if form.is_valid():
                action = request.POST.get('action', None)

                if action == 'delete':
                    question.delete()
                    return redirect('/questions/')
                elif action == 'copy':
                    form = QuestionEditForm(request.POST)
                    new = form.save()
                    for key in question.answer_keys.all():
                        key = copy.copy(key)
                        key.pk = None
                        key.question = new
                        key.save()
                        new.answer_keys.add(key)
                    new.owner = request.user
                    new.update()
                    return redirect('../../%s' % new.pk)
                elif action == 'view':
                    form.save().update()
                    return redirect('../')
                else:
                    form.save().update()
        else:
            form = QuestionEditForm(instance=question)

        context.update(extra_context or {}, form=form)
        return render(request, 'cs_questions/io/edit.jinja2', context)

    def edit_key(self, request, question, key):
        key = question.answer_keys.get(pk=key)
        context = {
            'question': question,
            'language': key.language,
            'key': key,
        }

        if request.method == 'POST':
            form = AnswerKeyEditForm(request.POST, instance=key)
            if form.is_valid():
                key = form.save()
                key.update()
                return redirect('../../edit')
        else:
            form = AnswerKeyEditForm(instance=key)

        context['form'] = form
        return render(request, 'cs_questions/io/edit-key.jinja2', context)

    def add_key(self, request, question):
        used_langs = question.answer_keys.select_related('language')
        languages = ProgrammingLanguage.objects.exclude(pk__in=used_langs)

        context = {
            'question': question,
            'languages': languages,
        }

        if request.method == 'POST':
            form = AnswerKeyAddForm(request.POST)
            if form.is_valid():
                key = question.answer_keys.create(
                    source=form.cleaned_data['source'],
                    placeholder=form.cleaned_data['placeholder'],
                    language=form.cleaned_data['language'],
                )
                key.update()
                return redirect('../edit')
        else:
            form = AnswerKeyAddForm()

        context['form'] = form
        return render(request, 'cs_questions/io/add-key.jinja2', context)

    def download(self, request, question):
        if request.user != question.owner:
            return http.HttpResponseForbidden()
        return http.HttpResponse(question.as_markio(),
                                 content_type='text/markdown')


