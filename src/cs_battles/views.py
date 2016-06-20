from django.shortcuts import render,redirect
from django.http import Http404,HttpResponse
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from cs_questions.models import Question, CodingIoResponseItem
from cs_core.models import ProgrammingLanguage
from .models import BattleResponse, Battle
from datetime import datetime
from viewpack import CRUDViewPack
from django.views.generic.edit import ModelFormMixin

from .forms import  BattleForm

def battle(request,battle_pk):
    if request.method == "POST":
        message = ""
        form = BattleForm(request.POST)
        if form.is_valid():
            battle_code = request.POST.get("code")
            time_now = datetime.now()
            battle = Battle.objects.get(id=battle_pk)

            battle_response = battle.battles.filter(user_id=request.user.id).first()
            battle_response.source = battle_code
            battle_response.question = battle.question
            battle_response.language=battle.language
            battle_response.time_end = time_now

            battle_response.autograde_response()
            battle_response.save()
            battle_is_corret = battle_response.is_correct
            if battle_is_corret:
                message = "Sua questão está certa"
            else:
                message = "Está errada"

        context = {
            'message':message,
        }
        return render(request, 'battles/result.jinja2', context)
    else:
        return render(request, 'battles/battle.jinja2')

def battle_user(request):
    """Define the battles of a user"""
    user = request.user
    battles = BattleResponse.objects.filter(user_id=user.id)
    context = {"battles": battles}
    return render(request, 'battles/battle_user.jinja2', context)


# View the invitations
def invitations(request):
    invitations_user = Battle.objects.filter(invitations_user=request.user.id).all()
    context = {'invitations': invitations_user}
    return render(request,'battles/invitation.jinja2', context)

# Accept the invitation
def battle_invitation(request):
    if request.method == "POST":
        form_post = request.POST
        battle_pk = form_post.get('battle_pk')
        method_return = None
        if form_post.get('accept'):
            battle = Battle.objects.get(id=battle_pk)
            create_battle_response(battle,request.user)
            method_return = redirect(reverse('cs_battles:battle',kwargs={'battle_pk':battle_pk}))
        elif battle_pk and form_post.get('reject'):
            battle_result = Battle.objects.get(id=battle_pk)
            battle_result.invitations_user.remove(request.user)
            method_return = redirect(reverse('cs_battles:view_invitation'))
    return method_return

def create_battle_response(battle,user):
    battle_response = battle.battles.filter(user_id=user.id)
    if not battle_response:
        battle_response = BattleResponse.objects.create(
            user=user,
            language=battle.language,
            source="",
            time_begin=timezone.now(),
            time_end=timezone.now(),
            battle=battle,
        )
    battle.invitations_user.remove(user)

class BattleCRUDView(CRUDViewPack):
    model = Battle
    template_extension = '.jinja2'
    template_basename = 'battles/'
    check_permissions = False
    raise_404_on_permission_error = False
    exclude_fields = ['battle_owner','battle_winner' ]

    class CreateMixin:

        def get_success_url(self):
            return reverse("cs_battles:battle",kwargs={'battle_pk': self.object.pk})

        def form_valid(self,form):
            self.object = form.save(commit=False)
            self.object.battle_owner = self.request.user
            self.object.save()
            create_battle_response(self.object,self.request.user)
            return super(ModelFormMixin, self).form_valid(form)

    class DetailViewMixin:
        def get_object(self,queryset=None):
            object = super().get_object(queryset)
            object.determine_winner()
            return object

        def get_context_data(self, **kwargs):
                return super().get_context_data(
                    all_battles=self.object.battles.all(),**kwargs)

