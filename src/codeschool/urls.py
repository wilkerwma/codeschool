from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView

from codeschool import views
from cs_search import views as search_views

urlpatterns = [
    # # Basic wagtail/django functionality
    url(r'^$', views.index, name='index'),
    url(r'^django-admin/', include(admin.site.urls)),
    url(r'^admin/', include('wagtail.wagtailadmin.urls')),
    url(r'^documents/', include('wagtail.wagtaildocs.urls')),
    url(r'^search/$', search_views.search, name='search'),

    # RPC and JSON api
    url(r'^srvice/', include('srvice.urls', namespace='srvice')),
    url(r'^api/pages/', include('wagtail.contrib.wagtailapi.urls')),

    # Authentication
    url(r'^accounts/', include('cs_core.urls', namespace='auth')),
    url(r'^accounts/', include('userena.urls', namespace=None)),

    # Local apps and functionality
    # url(r'^activities/', include('cs_activities.urls')),
    # url(r'^courses/', include('cs_courses.urls', namespace='course')),
    url(r'^courses/', RedirectView.as_view(url='/unb-gama/')),
    # url(r'^questions/', include('cs_questions.urls')),
    # url(r'^polls/', include('cs_polls.urls')),
    # url(r'^battles/', include('cs_battles.urls', namespace='battle')),
    # url(r'^pbl/', include('cs_pbl.urls', namespace='pbl')),
    url(r'', include('wagtail.wagtailcore.urls')),

]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
