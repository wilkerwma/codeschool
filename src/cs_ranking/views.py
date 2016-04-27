from django.shortcuts import render
from django.http import Http404
from .models import Battle,BattleResult

# Create your views here.
def index(request):
    all_battles =  BattleResult.objects.all()
    return render(request, 'ranking/index.jinja2',{"battles": all_battles})



# 'Controller' to view result of a battle
def battle_result(request,id_battle):
    print(id_battle)
    context={}
    try:
        result_battle = BattleResult.objects.get(id=id_battle)
        battles = result_battle.battles.all()

        if len(battles) == 2:
            # This process can be automatized
            win = determine_winner(battles[0].code_winner,battles[1].code_winner) # The code winner is 0 or 1
            loser = not win # The possible index are only 1 or 0, then the loser is the inverse of winner
 
            context={ "battle_winner": battles[win],"battle_loser":battles[loser],
                            "time_winner":battles[win].time_result(),"time_loser":battles[loser].time_result(),
                            "len_winner":len(battles[win].code_winner),"len_loser":len(battles[loser].code_winner)}
        else:
            raise Http404("All battles not found")
    except BattleResult.DoesNotExist as e:
        print("Not found battle"+str(e))
        raise Http404("Battle not found")

    return render(request,'ranking/battle_result.jinja2',context)

# Define the battles of a user
def battle_user(request):
    user = request.user
    battles = Battle.objects.filter(user_id=user.id)
    print(battles)
    context = {"battles": battles}
    return render(request, 'ranking/battle_user.jinja2', context)

def determine_winner(code_one="",code_two=""):
    winner_index=0 # Determine the index of the winner (0 or 1)

    if len(code_one) > len(code_two):
        winner_index=1
    else:
        winner_index=0

    return winner_index
