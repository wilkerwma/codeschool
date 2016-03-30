from django.shortcuts import render
from .models import Battle
# Create your views here.
def index(request):
    return render(request, 'ranking/index.html')

# 'Controller' to view result of a battle
def battle_result(request,id_battle):
    print(id_battle)
    try:
        result_battle = Battle.objects.get(id=id_battle)
        return render(request,'ranking/battle_result.html',{"battle":result_battle})
    except:
        print("Not found battle")
        return render(request,'ranking/index.html')
