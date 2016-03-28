"""
Control authentication and new users registrations.
"""

from django import http
from django.contrib import auth
from codeschool.decorators import login_required
from codeschool.shortcuts import render_context, redirect, get_object_or_404
from codeschool import models
from cs_auth import forms

users = models.User.objects
root_url = '/courses'


@login_required
def public_profile(request, user):
    user = get_object_or_404(models.User, username=user)
    return render_context(request, 'cs_auth/profile.jinja2',
        name=user.full_name,
        emai=user.email,
        courses=user.enrolled_courses.all(),
        profile=user.profile_type_name(),
    )


@login_required
def edit_profile(request):
    pass


def register(request):
    if request.method != 'POST':
        raise http.HttpResponseBadRequest

    # Load form and validate
    form = forms.RegisterForm(request.POST)
    if not form.is_valid():
        return index(request, register_form=form, selected_tab=1)

    # Process form
    username = form.cleaned_data['username']
    name = form.cleaned_data['name']
    surname = form.cleaned_data['surname']
    email = form.cleaned_data['email']
    password = form.cleaned_data['password']
    password_confirmation = form.cleaned_data['password_confirmation']

    # Check valid password
    if password != password_confirmation:
        form.add_error('password_confirmation', 'Senhas não conferem')
        return index(request, register_form=form, selected_tab=1)

    # Check user
    if request.user.is_authenticated():
        auth.logout(request)
    try:
        users.get(username=username)
        form.add_error('username', 'Usuário existente')
        return index(request, register_form=form, selected_tab=1)
    except User.DoesNotExist:
        user = users.create_user(username, email, password,
                                first_name=name,
                                last_name=surname)
        user.save()
        user = auth.authenticate(username=username, password=password)
        auth.login(request, user)
        return redirect(root_url)


def login(request):
    if request.method != 'POST':
        raise http.HttpResponseBadRequest

    # Load form and validate
    form = forms.LoginForm(request.POST)
    if not form.is_valid():
        return index(request, login_form=form)

    # Process form
    username = form.cleaned_data['username']
    password = form.cleaned_data['password']

    try:
        users.get(username=username)
        user = auth.authenticate(username=username, password=password)
        auth.login(request, user)
        return redirect(root_url)
    except models.User.DoesNotExist:
        pass
    form.add_error('username', 'Usuário ou senha inválidos')
    return index(request, login_form=form)


def index(request, login_form=None, register_form=None, selected_tab=0):
    return render_context(request, 'cs_auth/index.jinja2',
                          selected_tab=selected_tab,
                          login_form=login_form or forms.LoginForm(),
                          register_form=register_form or forms.RegisterForm())
