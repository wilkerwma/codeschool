from django.shortcuts import render
from codeschool.shortcuts import render_context
from django.shortcuts import get_object_or_404
from cs_linktable import models


def index(request):
    return render_context(
            request,
            'cs_linktable/index.jinja2',
            tables=list(models.Table.objects.all()))


def linktable(request, pk):
    table = get_object_or_404(models.Table, pk=pk)

    if request.method == 'POST':
        name = request.POST['name']
        url = request.POST['url']
        models.Row(name=name, url=url, table=table).save()
        
    return render_context(
            request,
            'cs_linktable/detail.jinja2',
            table=table)