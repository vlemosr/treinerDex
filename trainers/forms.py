from django import forms

from .models import Friend, PokedexRegistration, TrainerProfile


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


class PokedexRegistrationForm(forms.ModelForm):
    class Meta:
        model = PokedexRegistration
        fields = ('pokemon_number', 'nickname', 'notes', 'is_favorite')
        labels = {
            'pokemon_number': 'Número do Pokémon (1 a 649)',
            'nickname': 'Apelido (opcional)',
            'notes': 'Anotações da Captura',
            'is_favorite': 'Marcar como Favorito',
        }
        widgets = {
            'pokemon_number': forms.NumberInput(attrs={'min': 1, 'max': 649, 'placeholder': 'Ex: 25 para Pikachu'}),
            'nickname': forms.TextInput(attrs={'placeholder': 'Ex: Sparky'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Informações sobre a captura, habitat ou táticas'}),
        }


class PokedexRegistrationUpdateForm(forms.ModelForm):
    class Meta:
        model = PokedexRegistration
        fields = ('nickname', 'notes', 'is_favorite')
        labels = {
            'nickname': 'Apelido do Pokémon',
            'notes': 'Anotações da Captura',
            'is_favorite': 'Marcar como Favorito',
        }
        widgets = {
            'nickname': forms.TextInput(attrs={'placeholder': 'Ex: Sparky'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Informações sobre a captura, habitat ou táticas'}),
        }
