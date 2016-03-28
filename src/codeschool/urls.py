from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin
from django.views.generic.base import RedirectView

from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailcore import urls as wagtail_urls

from cs_search import views as search_views
from cs_auth import urls as auth_urls
from cs_courses import urls as courses_urls
from cs_questions import urls as questions_urls
from cs_linktable import urls as linktable_urls


urlpatterns = [
    # Basic wagtail/django functionality
    url(r'^$', RedirectView.as_view(url='/auth/', permanent=False)),
    url(r'^django-admin/', include(admin.site.urls)),
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'^search/$', search_views.search, name='search'),
    url(r'^cms/', include(wagtail_urls)),

    # Authentication
    url(r'^auth/', include(auth_urls)),
    url(r'^login/$', RedirectView.as_view(url='/auth/', permanent=False)),

    # Local apps and functionality
    url(r'^courses/', include(courses_urls)),
    url(r'^questions/', include(questions_urls)),
    url(r'^linktables/', include(linktable_urls)),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.views.generic import TemplateView

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
