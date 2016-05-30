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

from .forms import  BattleInvitationForm
# Principal method to battles
def index(request):
    all_battles = Battle.objects.all()
    invitations_user = invitations(request)
    return render(request, 'battles/index.jinja2', { "battles": all_battles,"invitations": invitations_user })

# Controller to view result of a battle
def battle_result(request,battle_pk):
    context = {}
    try:
        # Obtain the battles of battle result
        result_battle = Battle.objects.get(id=battle_pk)
        battles = result_battle.battles.all()

        # Determine the winner of this battle result based in the type (lenght, time resolution)
        context = { "battles": battles }
        if not result_battle.invitations_user.all():
            context["battle_winner"] = result_battle.determine_winner()

    except Battle.DoesNotExist as e:
        print("Not found battle"+str(e))
        raise Http404("BattleResponse not found")

    return render(request,'battles/battle_result.jinja2',context)

def battle(request,battle_pk):
    if request.method == "POST":
        print("Method POST")
        form = request.POST
        battle_code = form.get('code')
        if battle_code:
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
        print("Method GET")
        return render(request, 'battles/battle.jinja2')

# Define the battles of a user
def battle_user(request):
    user = request.user
    battles = BattleResponse.objects.filter(user_id=user.id)
    print(battles)
    context = {"battles": battles}
    return render(request, 'battles/battle_user.jinja2', context)


# Create a new invitation
def invitation_users(request):
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = BattleInvitationForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            battle = Battle()
            battle.date = timezone.now()
            # battle.type = request.POST.get('type')
            battle.type = "length"

            form_question = form.cleaned_data['question']
            battle.question = Question.objects.get(id=form_question.id)

            form_language = form.cleaned_data['language']
            battle.language = ProgrammingLanguage.objects.get(pk=form_language.name)

            battle.battle_owner = request.user

            battle.save()
            names = request.POST.get('usernames')
            users = []

            for name in names.split(";"):
                user = User.objects.filter(username=name.strip())
                if len(user):
                    users.append(user[0])

            [battle.invitations_user.add(user) for user in users]
            create_battle_response(battle,request.user)
            return redirect(reverse('fights:battle',kwargs={'battle_pk':battle.id})) 
    else:
        form = BattleInvitationForm()
        context = { "questions": Question.objects.all(),
                    "languages": ProgrammingLanguage.objects.all(),
                    "form": form
                  }
        return render(request,'ranking/invitation.jinja2', context)

# View the invitations
def invitations(request):
    print(request.user.id)
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
            user_id=user.id,
            source="",
            time_begin=timezone.now(),
            time_end=timezone.now(),
            battle=battle
        )
    battle.invitations_user.remove(user)

class BattleCRUDView(CRUDViewPack):
    model = Battle
    get_absolute_url = r'^'
    template_extension = '.jinja2'
    template_basename = 'battles/'
    check_permissions = False
    raise_404_on_permission_error = False
    exclude_fields = ['battle_owner','battle_winner' ]
    
    class CreateMixin:
        def form_valid(self,form):
            self.object = form.save(commit=False)
            self.object.battle_owner = self.request.user
            self.object.save()
            return super(ModelFormMixin, self).form_valid(form)
            
