from django.forms import ModelForm

class BattleInvitationForm(ModelForm):
    class Meta:
        model = Battle
        fields = ['question', 'battle_owner', 'language']

