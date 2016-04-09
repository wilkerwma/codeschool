from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin
from django.views.generic.base import RedirectView
from cs_search import views as search_views


urlpatterns = [
    # Basic wagtail/django functionality
    url(r'^$', RedirectView.as_view(url='/auth/', permanent=False)),
    url(r'^django-admin/', include(admin.site.urls)),
    url(r'^admin/', include('wagtail.wagtailadmin.urls')),
    url(r'^documents/', include('wagtail.wagtaildocs.urls')),
    url(r'^search/$', search_views.search, name='search'),
    url(r'^cms/', include('wagtail.wagtailcore.urls')),

    # RPC and api
    url(r'^srvice/', include('srvice.urls')),
    #url(r'^api/', include(core_urls.router.urls)),
    #url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Authentication
    url(r'^auth/', include('cs_auth.urls')),
    url(r'^login/$', RedirectView.as_view(url='/auth/', permanent=False)),

    # Local apps and functionality
    url(r'^courses/', include('cs_courses.urls')),
    url(r'^questions/', include('cs_questions.urls')),
    url(r'^linktables/', include('cs_linktable.urls')),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.views.generic import TemplateView

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
