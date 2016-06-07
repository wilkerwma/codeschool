### Comentarios:
# Talvez devessemos trocar este modulo por um modulo de factories usando o
# FactoryBoy. Por enquanto estou usando as factories apenas no contexto de testes,
# mas cabe em outros lugares como popular bancos de dados iniciais.
#
# Veja como fazer em codeschool/factories.py
###


# Determine the seeds to test data
import django
from django.conf import settings

import os
NAMES = ["João", "Ana","Amanda","Letícia","Roberta","Pedro","Marcelo","Rayanne"]
LAST_NAMES = ["Ferreira","Silva","Solza","Gomes","Bastos","Barreto","Campos","Pereira"]
PASSWORD="asdf"

users = []
battles_result = []
battles = []

def seed():
    global battles_result
    create_users(10) 
    for u in users:
        u.set_password(PASSWORD)
        u.save()

    create_battles_result(10)
    for br in battles_result:
        br.save()
   
    create_battles(battles_result)

    for b in battles:
        b.save()


def create_users(amount):
    global users
    last_index = User.objects.order_by("-id")[0].id
    print("Generating the users")
    for i in range(amount):
        print("user%d" % (last_index+1))
        users.append(User(password=PASSWORD,username="user"+str(last_index+1),first_name=NAMES[i%8],last_name=LAST_NAMES[i%8],email="user"+str(last_index+1)+"@m.c"))
        last_index+=1

def create_battles(battles_result):
    global battles
    result = 0

    print("Creating the battles")
    for i in battles_result:
        b = BattleResponse(user = users[result],battle_result = i,code_winner="if()while()for()",time_begin=timezone.now(),time_end=timezone.now()+timezone.timedelta(2))
        result+=1
        d = BattleResponse(user = users[result],battle_result = i,code_winner="if()while()for()",time_begin=timezone.now(),time_end=timezone.now()+timezone.timedelta(2))
        battles.append(b)
        battles.append(d)
        result+=1
    
def create_battles_result(amount):
    global battles_result
    print("Creating the battles result")
    for i in range(int(amount/2)):
        battles_result.append(Battle())
            
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codeschool.settings")
    django.setup()

#    if not settings.configured:
#        settings.configure(base,DEGUB=True)
    from cs_battles.models import BattleResponse,Battle
    from django.contrib.auth.models import User
    from django.utils import timezone
#    from codeschool.settings import base

    seed()
    print(BattleResponse.objects.all())
    print(User.objects.all())

