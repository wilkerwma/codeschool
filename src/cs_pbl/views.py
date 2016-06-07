from django.shortcuts import render
from django.contrib.auth.models import User
from cs_pbl import models
from codeschool.decorators import login_required

@login_required
def badge_detail(request):
    pass 

def index(request):
    badge = get_object_or_404(models.Badge, pk=pk)
    return render_context(
        request,
        'cs_pbl/index.jinja2',
        badge=badge,
        #badges=models.Badge.objects.all().order_by('pk')
    )
