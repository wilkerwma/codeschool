from django.shortcuts import render,redirect
from django.http import Http404,HttpResponse
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from cs_questions.models import Question, CodingIoResponse
from cs_core.models import ProgrammingLanguage
from .models import BattleResponse,Battle
from datetime import datetime
from viewpack import CRUDViewPack
from django.views.generic.edit import ModelFormMixin

from .forms import  BattleForm

def battle(request,battle_pk):
    if request.method == "POST":
        form = BattleForm(request.POST)
        battle_code = form.cleaned_data['source']
        if battle_code.is_valid():
            time_now = datetime.now()
            battle_result = Battle.objects.get(id=battle_pk)

            coding = CodingIoResponse.objects.create(
                question=battle_result.question,
                user_id=1,
                language_id=battle_result.language
            )
            asdfdsa = coding.is_correct

            battle = BattleResponse.objects.create(
                user=request.user,
                battle_code=battle_code,
                time_begin=time_now,
                time_end=time_now,
                battle_result=battle_result
            )

        return render(request, 'battles/battle.jinja2')
    else:
        return render(request, 'ranking/battle.jinja2')

# Define the battles of a user
def battle_user(request):
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
            method_return = redirect(reverse('fights:battle',kwargs={'battle_pk':battle_pk}))
        elif battle_pk and form_post.get('reject'):
            battle_result = Battle.objects.get(id=battle_pk)
            battle_result.invitations_user.remove(request.user)
            method_return = redirect(reverse('fights:view_invitation'))

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
            battle=battle
        )
    battle.invitations_user.remove(user)

class BattleCRUDView(CRUDViewPack):
    model = Battle
 #   get_absolute_url = r'^'
    template_extension = '.jinja2'
    template_basename = 'battles/'
    check_permissions = False
    raise_404_on_permission_error = False
    exclude_fields = ['battle_owner','battle_winner' ]
    """def get_absolute_url(self):
        return '/battles/'#reverse("figths:battle",kwargs={'battle_pk': self.pk})
    """

    class CreateMixin:

        def get_success_url(self):   
            return reverse("figths:battle",kwargs={'battle_pk': self.object.pk})

        def form_valid(self,form):
            self.object = form.save(commit=False)
            self.object.battle_owner = self.request.user
            self.object.save()
            create_battle_response(self.object,self.request.user)
            return super(ModelFormMixin, self).form_valid(form)
            
