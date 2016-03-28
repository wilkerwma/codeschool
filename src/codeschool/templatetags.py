from crispy_forms.utils import render_crispy_form
from jinja2 import contextfunction
from django_jinja import library


@contextfunction
@library.global_function
def crispy(context, form):
    '''Renders crispy forms on Jinja2'''
    
    return render_crispy_form(form, context=context)