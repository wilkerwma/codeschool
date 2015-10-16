from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from . import models

class NewAccountForm(forms.Form):
    '''Form used to create a new accounts to codeschool'''
    
    first_name = forms.CharField(
        label='Primeiro nome',
        max_length=200,
        required=True,
    )
    
    last_name = forms.CharField(
        label='Último nome', 
        max_length=200,
        required=True,
    )
    
    username = forms.CharField(
        label='Matrícula (sem a barra)', 
        max_length=200,
        required=True,
    )
    
    email = forms.EmailField()
    
    password = forms.CharField(
        label='Senha', 
        max_length=200, 
        widget=forms.PasswordInput,
        required=True,
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-new-account'
        self.helper.form_method = 'post'
        self.helper.form_action = '/new account/'
        self.helper.add_input(Submit('submit', 'Criar nova conta'))


class SubmitQuestionForm(forms.Form):
    '''Form used to insert answers in students responses.'''

    partner_name = forms.CharField(
        label='Nome/matrícula', 
        max_length=200,
        required=False,
        error_messages={
            'required': 'Você deve registrar pelo menos um nome!'
        }
    )
    
    partner_username = forms.CharField(
        label='Matrícula', 
        max_length=20,
        required=False,
        error_messages={
            'required': 'Digite a matrícula!'
        }
    )

    response = forms.CharField(
        label='Caixa de resposta',
        widget=forms.Textarea(
            attrs={
                'cols': 80, 
                'rows': 25, 
                'name': 'code'
            }
        ),
        initial='# Digite ou cole a sua solução aqui\n'
    )
