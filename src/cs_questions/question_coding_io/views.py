import copy
from codeschool.shortcuts import redirect, render
from codeschool.urlsubclassmapper import ViewMapper
from cs_core.models import ProgrammingLanguage
from cs_questions.question_coding_io.forms import \
    QuestionEditForm, AnswerKeyEditForm, AnswerKeyAddForm
from cs_activities.views import mapper as activities_mapper
from cs_questions.question_coding_io.models import CodingIoQuestion, CodingIoActivity
from cs_questions.views import QuestionViews, mapper


@mapper.register(name='io', model=CodingIoQuestion)
class CodingIoQuestionViews(QuestionViews):
    model_form = QuestionEditForm

    def read_model(self, data):
        question = None
        try:
            question = CodingIoQuestion.from_markio(data)
            question.update(validate=True)
        except Exception as ex:
            ex = ex if isinstance(ex, SyntaxError) else ''
            self['import_ok'] = False
            self['import_error'] = 'This is not a valid Markio source. ' + ex
        else:
            self['import_ok'] = True
            question.delete()
        return question

    def copy_data_from(self, new, old):
        for key in old.answer_keys.all():
            key = copy.copy(key)
            key.pk = None
            key.question = new
            key.save()
            new.answer_keys.add(key)

    def view_edit(self, obj):
        used_langs = obj.answer_keys.select_related('language')
        languages = ProgrammingLanguage.objects.exclude(pk__in=used_langs)
        self.context.update({
            'add_button': bool(languages),
            'show_answer_keys': True,
        })
        return super().view_edit(obj)

    def view_detail(self, obj):
        self.context.update({
            'lang': None,
            'languages': ProgrammingLanguage.objects.all(),
        })
        return super().view_detail(obj)

    def view_edit_key(self, question, key):
        key = question.answer_keys.get(pk=key)
        self.context.update({
            'question': question,
            'language': key.language,
            'key': key,
        })

        if self.request.method == 'POST':
            form = AnswerKeyEditForm(self.request.POST, instance=key)
            if form.is_valid():
                key = form.save()
                key.update()
                return redirect('../../edit')
        else:
            form = AnswerKeyEditForm(instance=key)

        self.context['form'] = form

        return render(self.request, 'cs_questions/io/edit-key.jinja2', self.context)

    def view_add_key(self, question):
        used_langs = question.answer_keys.select_related('language')
        languages = ProgrammingLanguage.objects.exclude(pk__in=used_langs)

        self.context.update(question=question, languages=languages)

        if self.request.method == 'POST':
            form = AnswerKeyAddForm(self.request.POST)
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

        self.context['form'] = form

        return render(self.request, 'cs_questions/io/add-key.jinja2', self.context)


@activities_mapper.register(model=CodingIoActivity, name='io')
class CodingIoActivityViews(ViewMapper):
    pass