from django.shortcuts import render
from django.http import Http404
from .models import Battle,BattleResult

# Principal method to battles
def index(request):
    all_battles = BattleResult.objects.all()
    return render(request, 'ranking/index.jinja2', { "battles": all_battles })

# Controller to view result of a battle
def battle_result(request,id_battle):
    context = {}
    try:
        # Obtain the battles of battle result
        result_battle = BattleResult.objects.get(id=id_battle)
        battles = result_battle.battles.all()
        
        # Determine the winner of this battle result based in the type (lenght, time resolution)
        winner = result_battle.determine_winner(battles)
        
        context = { "battles": battles,"battle_winner": winner}

    except BattleResult.DoesNotExist as e:
        print("Not found battle"+str(e))
        raise Http404("Battle not found")

    return render(request,'ranking/battle_result.jinja2',context)

def battle(request):
    return render(request, 'ranking/battle.jinja2')

# Define the battles of a user
def battle_user(request):
    user = request.user
    battles = Battle.objects.filter(user_id=user.id)
    print(battles)
    context = {"battles": battles}
    return render(request, 'ranking/battle_user.jinja2', context)


