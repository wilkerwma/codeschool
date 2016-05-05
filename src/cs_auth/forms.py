from collections import OrderedDict
from django import forms
from django.utils.translation import ugettext_lazy as _
from userena.forms import SignupForm as _SignupForm
from cs_auth.models import Profile


class SignupForm(_SignupForm):
    """
    We create a new SignupForm since we want to have required first and last
    names.
    """
    _field_ordering = ['first_name', 'last_name']
    _field_ordering.extend(_SignupForm.base_fields)

    first_name = forms.CharField(
        label=_('First name'),
        max_length=100,
    )
    last_name = forms.CharField(
        label=_('Last name'),
        max_length=100,
    )

# Reorder fields
SignupForm.base_fields = OrderedDict(
    (k, SignupForm.base_fields[k]) for k in SignupForm._field_ordering
)


class SignupOptionalForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['gender', 'date_of_birth', 'about_me']