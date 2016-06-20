from django.forms import ModelForm
from cs_questions.question_coding_io.models import CodingIoQuestion, CodingIoAnswerKey, CodingIoResponse


class CodingIoResponseForm(ModelForm):
    class Meta:
        model = CodingIoResponse
        fields = ['language', 'source']


class AnswerKeyEditForm(ModelForm):
    class Meta:
        model = CodingIoAnswerKey
        fields = ['source', 'placeholder']


class AnswerKeyAddForm(ModelForm):
    class Meta:
        model = CodingIoAnswerKey
        fields = ['language', 'source', 'placeholder']
