Django's class based generic views are a great way to reuse code and avoid
boilerplate. In Django, however, each view is associated with a single URL. If
you want to reuse some behavior that involves multiple urls it is often
necessary to synchronize many different views. Think about a CRUD interface: it
is not necessarily hard, but it can be both tedious and error prone.

View packs gather a collection of views and url entry points together in a single
reusable unity. Hence, instead of creating separate CreateView, DetailView,
UpdateView, DeleteView, etc, we can simply subclass the CRUDViewPack view pack::

    from viewpack import CRUDViewPack
    from fooapp.models import FooModel


    class FooCRUD(CRUDViewPack):
        model = FooModel

In your urls.py, register all CRUD views as an include::

    from django.conf import url
    from views import FooCRUD


    urlpatterns = [
        ...,
        url(r'^foo/', FooCRUD.as_include(namespace='foo')),
    ]

Now you have registered a simple CRUD interface for your `FooModel`. The next
step is to write the required templates and you're done! (In fact, if you are
lazy and use Jinja, we even offer a few ready to use templates!)