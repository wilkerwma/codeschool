from datetime import datetime
from django.shortcuts import render,redirect
from django.http import Http404,HttpResponse
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from cs_battles.models import BattleResponse, CodingIoBattle

# Principal method to battles
def index(request):
    all_battles = CodingIoBattle.objects.all()
    invitations_user = invitations(request)
    return render(request, 'ranking/index.jinja2', { "battles": all_battles,"invitations": invitations_user })

# Controller to view result of a battle
def battle_result(request,id_battle):
    context = {}
    try:
        # Obtain the battles of battle result
        result_battle = CodingIoBattle.objects.get(id=id_battle)
        battles = result_battle.battles.all()

        # Determine the winner of this battle result based in the type (lenght, time resolution)
        winner = result_battle.determine_winner()
        
        context = { "battles": battles,"battle_winner": winner}

    except CodingIoBattle.DoesNotExist as e:
        print("Not found battle"+str(e))
        raise Http404("BattleResponse not found")

    return render(request,'ranking/battle_result.jinja2',context)

def battle(request,battle_pk):
    if request.method == "POST":
        print("Method POST")
        form = request.POST
        battle_code = form.get('code')
        if battle_code:
            time_now = datetime.now()
            battle_result = CodingIoBattle.objects.get(id=1)

            battle = BattleResponse.objects.create(
                user=request.user,
                battle_code=battle_code,
                time_begin=time_now,
                time_end=time_now,
                battle_result=battle_result
            )

        return render(request, 'ranking/battle.jinja2')
    else:
        print("Method GET")
        return render(request, 'ranking/battle.jinja2')

# Define the battles of a user
def battle_user(request):
    user = request.user
    battles = BattleResponse.objects.filter(user_id=user.id)
    print(battles)
    context = {"battles": battles}
    return render(request, 'ranking/battle_user.jinja2', context)


# Create a new invitation
def invitation_users(request):
    if request.method == "POST":

        battle = CodingIoBattle()
        battle.date = timezone.now()
        battle.type = request.POST.get('type')
        battle.question = request.POST.get('question') 
        battle.save()

        names = request.POST.get('usernames')
        print(names)
        users = [request.user]

        for name in names.split(";"):
            user = User.objects.filter(username=name.strip())
            if len(user):
                users.append(user[0])

        [battle.invited_users.add(user) for user in users]
        create_battle_response(battle,request.user)
        return redirect(reverse('fights:battle',kwargs={'battle_pk':battle.id})) 
    else:
        return render(request,'ranking/invitation.jinja2')

# View the invitations
def invitations(request):
    print(request.user.id)
    invited_users = CodingIoBattle.objects.filter(invited_users=request.user.id).all()
    return invited_users

# Accept the invitation
def battle_invitation(request):
    if request.method == "POST":
        form_post = request.POST
        id_battle = form_post.get('id_battle')
        method_return = None
        if form_post.get('accept'):
            battle = CodingIoBattle.objects.get(id=id_battle)
            create_battle_response(battle,request.user)
            method_return = redirect(reverse('fights:battle',kwargs={'battle_pk':id_battle}))
        elif id_battle and form_post.get('reject'):
            battle_result = CodingIoBattle.objects.get(id=id_battle)
            battle_result.invited_users.remove(request.user)
            method_return = redirect("/battle/")
        
    return method_return

def create_battle_response(battle,user):
    battle_response = battle.battles.filter(user_id=user.id)
    if not battle_response:
        battle_response = BattleResponse.objects.create(
            user=user,
            battle_code="",
            time_begin=timezone.now(),
            time_end=timezone.now(),
            battle_result=battle
        )
    battle.invited_users.remove(user)

