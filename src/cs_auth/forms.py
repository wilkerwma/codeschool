from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Matrícula',
        max_length=20,
        required=True,
    )
    password = forms.CharField(
        label='Senha',
        max_length=100,
        widget=forms.PasswordInput,
    )


class RegisterForm(forms.Form):
    username = forms.CharField(
        label='Matrícula',
        max_length=20,
        required=True,
    )

    email = forms.EmailField(
        required=True,
    )

    name = forms.CharField(
        label='Nome',
        max_length=200,
        required=True,
    )

    surname = forms.CharField(
        label='Sobrenome',
        max_length=200,
        required=True,
    )

    password = forms.CharField(
        label='Senha',
        max_length=100,
        widget=forms.PasswordInput,
        required=True,
    )

    password_confirmation = forms.CharField(
        label='Confirme a senha',
        max_length=100,
        widget=forms.PasswordInput,
        required=True,
    )
