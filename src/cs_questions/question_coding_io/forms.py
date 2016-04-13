from django.forms import ModelForm
from django import forms
from cs_questions.question_coding_io.models import CodingIoQuestion, CodingIoAnswerKey


class ImportQuestionForm(forms.Form):
    file = forms.FileField()


class QuestionEditForm(ModelForm):
    class Meta:
        model = CodingIoQuestion
        fields = ['title', 'short_description', 'long_description',
                  'discipline', 'iospec_source', 'iospec_size', 'timeout']


class AnswerKeyEditForm(ModelForm):
    class Meta:
        model = CodingIoAnswerKey
        fields = ['source', 'placeholder']


class AnswerKeyAddForm(ModelForm):
    class Meta:
        model = CodingIoAnswerKey
        fields = ['language', 'source', 'placeholder']
