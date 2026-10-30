from django import forms

from .models import Friend, TrainerProfile


class TrainerProfileForm(forms.ModelForm):
    class Meta:
        model = TrainerProfile
        fields = ('trainer_name', 'gender', 'city', 'clan')
        labels = {
            'trainer_name': 'Nome do treinador',
            'gender': 'Genero',
            'city': 'Cidade',
            'clan': 'Cla',
        }


class TrainerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = TrainerProfile
        fields = ('trainer_name', 'city', 'clan')
        labels = {
            'trainer_name': 'Nome do treinador',
            'city': 'Cidade',
            'clan': 'Cla',
        }


class FriendForm(forms.ModelForm):
    class Meta:
        model = Friend
        fields = ('name', 'nickname', 'clan', 'city', 'level', 'notes')
        labels = {
            'name': 'Nome',
            'nickname': 'Apelido',
            'clan': 'Clã',
            'city': 'Cidade',
            'level': 'Nível',
            'notes': 'Observações',
        }
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Informações adicionais sobre o treinador'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nickname'].required = True
        self.fields['clan'].required = True
        self.fields['city'].required = True
        self.fields['level'].widget.attrs.update({'min': 1})
