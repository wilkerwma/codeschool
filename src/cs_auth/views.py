"""
Control authentication and new users registrations.
"""

from userena.views import AuthenticationForm, SignupForm
from codeschool.shortcuts import render_context


def login(request):
    return render_context(
            request, 'cs_auth/login_page.jinja2',
            signin=AuthenticationForm(),
            signup=SignupForm(),
    )

