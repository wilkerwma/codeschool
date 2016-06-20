from django.core.urlresolvers import reverse
from django.template import loader
from codeschool.models import AnonymousUser
from codeschool.shortcuts import redirect


def index(request):
    """
    Codeschool index page.
    """
    # It redirects to the login page or to the profile page. It should probably
    # do something more interesting in the future.

    if isinstance(request.user, AnonymousUser):
        return redirect(reverse('auth:login'))
    else:
        return redirect('/unb-gama/')
