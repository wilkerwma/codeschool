from django.forms import ModelForm
from cs_battles.models import Battle

class BattleForm(ModelForm):
    class Meta:
        model = Battle
        fields = ['source']
