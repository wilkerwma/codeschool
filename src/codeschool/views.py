from codeschool.models import AnonymousUser
from codeschool.shortcuts import redirect
from django.core.urlresolvers import reverse


def index(request):
    """
    Codeschool index page.
    """
    # It redirects to the login page or to the profile page. It should probably
    # do something more interesting in the future.

    if isinstance(request.user, AnonymousUser):
        return redirect(reverse('auth:login'))
    else:
        username = request.user.username
        kwargs = {'username': username}
        return redirect(reverse('auth:userena_profile_detail', kwargs=kwargs))
