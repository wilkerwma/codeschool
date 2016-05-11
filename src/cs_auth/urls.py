from django.conf.urls import url
from cs_auth.views import LoginView
from userena import views as views
from userena.urls import urlpatterns as userena_patterns


urlpatterns = [
    url(r'^login/$', LoginView.as_view(), name='login'),
]

# Create a list of userena patterns and remove some patterns we don't want to
# use
blacklist = {'userena_signup', 'userena_signin'}
userena_patterns = list(userena_patterns)

# Now we loop over this patterns and include them in our urlpatterns
for x in userena_patterns:
    if x.name in blacklist:
        continue
    new = object.__new__(type(x))
    for (k, v) in x.__dict__.items():
        setattr(new, k, v)
    name = x.name.partition('_')[-1]
    name = name.replace('_', '-')
    new.name = name
    urlpatterns.append(new)
