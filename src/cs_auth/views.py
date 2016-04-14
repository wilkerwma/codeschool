"""
Control authentication and new users registrations.
"""

from django import http
from userena.forms import AuthenticationForm
from userena import views
from codeschool.shortcuts import render, redirect
from codeschool.models import User
from cs_auth.forms import SignupForm, SignupOptionalForm


def login(request):
    context = {'signin': AuthenticationForm(),
               'signup': SignupForm(),
               'signup_opt': SignupOptionalForm()}

    if request.method == 'POST':
        if request.POST['action-type'] == 'signup':
            form = SignupOptionalForm(request.POST)

            if not form.is_valid():
                context['signup'] = SignupOptionalForm(request.POST)
                context['signup_opt'] = form
                context['default_tab'] = 1
            else:
                context['signup_opt'] = SignupOptionalForm(request.POST)
                context['action'] = 'signup'
                context['default_tab'] = 1
                response = views.signup(
                        request,
                        signup_form=SignupForm,
                        template_name='cs_auth/login.jinja2',
                        extra_context=context,
                )

                # It redirects on success: we intercept add the extra
                # information
                if isinstance(response, http.HttpResponseRedirect):
                    # Fill extra info in signup form
                    aux = request.POST
                    success_url = '/accounts/%s' % aux['username']
                    user = User.objects.get(username=aux['username'])
                    user.first_name = aux['first_name']
                    user.last_name = aux['last_name']

                    # Fill extra profile info
                    form = SignupOptionalForm(request.POST)
                    form.is_valid()
                    aux = form.cleaned_data
                    user.profile.about_me = aux['about_me']
                    user.profile.gender = aux['gender']
                    user.profile.date_of_birth = aux['date_of_birth']

                    # Save modifications and go
                    user.save()
                    user.profile.save()

                    return redirect(success_url)
                return response
        else:
            context['action'] = 'signin'
            return views.signin(
                    request,
                    template_name='cs_auth/login.jinja2',
                    extra_context=context,
            )

    return render(request, 'cs_auth/login.jinja2', context)


def index(request):
    if request.user is None:
        return redirect('/accounts/login/')
    else:
        return redirect('/accounts/%s/' % request.user.username)
