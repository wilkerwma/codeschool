from django.conf.urls import url
from django.shortcuts import render
from userena import views as views
from userena.urls import urlpatterns as userena_patterns
from cs_core.views import LoginView
from cs_core.forms import EditProfileForm


urlpatterns = [
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^(?P<username>[\@\.\w-]+)/edit/$',
        views.profile_edit,
        {'edit_profile_form': EditProfileForm},
        name='profile-edit')

]

# Let us create a personalized list of userena patterns and remove some
# patterns we don't want to use
blacklist = {'userena_signup', 'userena_signin'}
userena_patterns = list(userena_patterns)

for url_pattern in userena_patterns:
    if url_pattern.name in blacklist:
        continue
    new = object.__new__(type(url_pattern))
    for (k, v) in url_pattern.__dict__.items():
        setattr(new, k, v)
    name = url_pattern.name.partition('_')[-1]
    name = name.replace('_', '-')
    new.name = name
    urlpatterns.append(new)
