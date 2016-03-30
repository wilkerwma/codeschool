from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'ranking/index.html')
def battle_result(request):
    return render(request,'ranking/battle_result.html')
