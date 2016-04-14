from django import forms
from django.utils.translation import ugettext_lazy as _


class ImportQuestionForm(forms.Form):
    file = forms.FileField(_('File'))
