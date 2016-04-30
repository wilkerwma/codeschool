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

        # This process can be automatized
        win = winner_length(battles)
 
        context = { "battles": battles,"battle_winner": battles[win]}
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

def winner_length(battles):
    
    winner_index=0 # Determine the index of the win ( any number 0..len(battles)-1)
    bigger_length = len(battles.first().code_winner)
    for index in range(1,len(battles)):
        code_length = len(battles[index].code_winner)
        if  code_length < bigger_length:
            bigger_length = code_length
            winner_index 
    return winner_index
