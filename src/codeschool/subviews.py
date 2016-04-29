"""
View groups
===========

Django views are functions that receive a request object and return an
HttpResponse. Class-based views are factory classes that instantiate objects
that can behave as Django functions. The main reason for doing this is to use
class inheritance in order to reuse common patterns. This is often more
convenient and less error-prone than fixing arguments of some complicated view
function.

ViewGroup take this idea one step further and create reusable collections of
views. These views can be either class based or regular view functions. Instead
of handling a single URL, ViewGroups handle all sub-urls bellow some entry point
and dispatch the results to some specific sub-view.


A basic view group
------------------

Consider this very simple example::

    class LinkedList(SingleObjectTemplateResponseMixin. ViewGroup):

        @view(r'^\d+/next')
        def next(self, request):
            return redirect('../%s' % self.object.next.pk)
"""




