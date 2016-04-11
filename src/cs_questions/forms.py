import copy
from django.forms import ModelForm
from django import forms
from cs_questions.models import CodingIoQuestion, CodingIoActivity
from cs_questions.admin import CodingIoQuestionAdmin


class ImportQuestionForm(forms.Form):
    file = forms.FileField()


class CodeIoQuestionForm(ModelForm):
    class Meta:
        model = CodingIoQuestion
        fields = ['title', 'short_description', 'long_description',
                  'discipline', 'iospec', 'iospec_size', 'timeout']
