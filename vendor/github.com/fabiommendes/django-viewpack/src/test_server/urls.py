"""viewgroups_test_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include

from test_app import views

urlpatterns = [
    # Test insertion as sub-view
    url(r'^as-view/(\d+)/$', views.TestViewPack.as_view('detail')),
    url(r'^as-view/(\d+)/edit/$', views.TestViewPack.as_view('edit')),
    url(r'^as-include/', views.TestViewPack.as_include(namespace='test-view')),
    url(r'^crud/', views.TestCRUDGroup.as_include(namespace='crud')),
    url(r'^subclass/', views.TestCRUDInheritanceGroup.as_include(
        namespace='subclass-crud')),
]
