from django import forms
from django.utils.translation import ugettext_lazy as _
from userena.forms import SignupForm as _SignupForm
from userena.forms import (USERNAME_RE, attrs_dict)
from cs_auth.models import Profile


class SignupForm(forms.Form):
    first_name = forms.CharField(
        label=_('First name'),
        max_length=100,
    )
    last_name = forms.CharField(
        label=_('Last name'),
        max_length=100,
    )
    username = forms.RegexField(
        regex=USERNAME_RE,
        max_length=30,
        widget=forms.TextInput(attrs=attrs_dict),
        label=_("Username"),
        error_messages={
            'invalid': _('Username must contain only letters, numbers, dots '
                         'and underscores.')
        }
    )
    email = forms.EmailField(
        widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=75)),
        label=_("Email")
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs=attrs_dict,
        render_value=False),
        label=_("Create password")
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs=attrs_dict,
        render_value=False),
        label=_("Repeat password")
    )

    # Patch methods from SignupForm
    clean_username = _SignupForm.clean_username
    clean_email = _SignupForm.clean_email
    clean = _SignupForm.clean
    save = _SignupForm.save


class SignupOptionalForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['gender', 'date_of_birth', 'about_me']