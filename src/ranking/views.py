from django.shortcuts import render
from django.http import Http404
from .models import Battle
# Create your views here.
def index(request):
    return render(request, 'ranking/index.html')

# 'Controller' to view result of a battle
def battle_result(request,id_battle):
    print( id_battle)
    try:
        result_battle = Battle.objects.get(id=id_battle)
        response_dict ={"battle": result_battle,
                        "time_result": result_battle.time_result(),
                        "len_code": len(result_battle.code_winner) }
    except Battle.DoesNotExist as e:
        print("Not found battle"+str(e))
        raise Http404("Battle not found")

    return render(request,'ranking/battle_result.html',response_dict)
 
