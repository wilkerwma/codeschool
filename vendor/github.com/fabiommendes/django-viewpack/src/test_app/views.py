from django.shortcuts import render, get_object_or_404
from django import http
from viewpack import ViewPack, CRUDViewPack, InheritanceCRUDViewPack, View, view
from test_app.models import TestModel


class TestViewPack(ViewPack):
    @view(r'^(\d+)/$')
    def detail(self, request, pk):
        obj = get_object_or_404(TestModel.objects, pk=pk)
        data = 'name: %s<br>description: %s' % (obj.name, obj.description)
        return http.HttpResponse(data)

    @view(r'^(\d+)/edit/$')
    class EditView(View):
        def get(self, request, pk):
            return http.HttpResponse('edit form')

        def post(self, request, pk):
            obj = get_object_or_404(TestModel.objects, pk=pk)
            obj.name = request.POST['name']
            obj.description = request.POST['description']
            return self.parent.detail(request, pk)


class TestCRUDGroup(CRUDViewPack):
    model = TestModel
    template_extension = '.jinja2'
    template_basename = 'app/testmodel_'


class TestCRUDInheritanceGroup(InheritanceCRUDViewPack):
    model = TestModel
    template_extension = '.jinja2'
    template_basename = 'app/testmodel_'


@TestCRUDInheritanceGroup.register
class Test1(CRUDViewPack):
    model = TestModel