import copy
from codeschool.shortcuts import redirect, render
from cs_core.models import ProgrammingLanguage
from cs_questions.question_coding_io.forms import (
    QuestionEditForm, AnswerKeyEditForm, AnswerKeyAddForm
)
from cs_questions.question_coding_io.models import CodingIoQuestion
from cs_questions.views import QuestionViews


class CodingIoQuestionViews(QuestionViews):
    name = 'io'
    model = CodingIoQuestion
    form_model = QuestionEditForm
    exclude_fields = QuestionViews.exclude_fields + ('status', 'status_changed')

    def import_question(self, data, context):
        question = None
        try:
            question = CodingIoQuestion.from_markio(data)
            question.update(validate=True)
        except Exception as ex:
            ex = ex if isinstance(ex, SyntaxError) else ''
            context['import_ok'] = False
            context['import_error'] = 'This is not a valid Markio source. ' + ex
        else:
            context['import_ok'] = question.status == question.STATUS_VALID
            context['import_error'] = question.status
            question.delete()
        return question

    def copy_data_from(self, new, old):
        for key in old.answer_keys.all():
            key = copy.copy(key)
            key.pk = None
            key.question = new
            key.save()
            new.answer_keys.add(key)

    def view_edit(self, request, question, extra_context=None, **kwds):
        used_langs = question.answer_keys.select_related('language')
        languages = ProgrammingLanguage.objects.exclude(pk__in=used_langs)
        context = {
            'add_button': bool(languages),
            'show_answer_keys': True,
        }
        context.update(extra_context or {})

        return super().view_edit(request, question, context, **kwds)

    def view_detail(self, request, question, extra_context=None, **kwds):
        context = {
            'lang': None,
            'languages': ProgrammingLanguage.objects.all(),
        }
        context.update(extra_context or {})

        return super().view_detail(request, question, context, **kwds)

    def view_edit_key(self, request, question, key, extra_context=None):
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
        context.update(extra_context or {})

        return render(request, 'cs_questions/io/edit-key.jinja2', context)

    def view_add_key(self, request, question, extra_context=None):
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
        context.update(extra_context or {})

        return render(request, 'cs_questions/io/add-key.jinja2', context)

