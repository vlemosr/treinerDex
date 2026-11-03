from django import forms

from .models import Friend, PokedexRegistration, TrainerProfile
from .services.pokedex import find_pokemon_by_name, find_pokemon_by_number


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
        fields = ('name', 'level', 'clan', 'city', 'notes')
        labels = {
            'name': 'Nome do amigo',
            'level': 'Nível',
            'clan': 'Clã',
            'city': 'Cidade',
            'notes': 'Observações',
        }
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Informações adicionais sobre o treinador'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['clan'].required = True
        self.fields['city'].required = True
        self.fields['level'].widget.attrs.update({'min': 1})

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.data and 'nickname' in self.data:
            instance.nickname = self.data.get('nickname')
        if commit:
            instance.save()
        return instance


class PokedexRegistrationForm(forms.ModelForm):
    pokemon_name = forms.CharField(
        label='Nome do Pokémon',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Pikachu, Charizard, Lucario...',
            'list': 'pokemon-name-list',
            'autocomplete': 'off',
        }),
    )

    class Meta:
        model = PokedexRegistration
        fields = ('pokemon_name', 'nickname', 'notes', 'is_favorite')
        labels = {
            'pokemon_name': 'Nome do Pokémon',
            'nickname': 'Apelido (opcional)',
            'notes': 'Anotações da Captura',
            'is_favorite': 'Marcar como Favorito',
        }
        widgets = {
            'nickname': forms.TextInput(attrs={'placeholder': 'Ex: Sparky'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Informações sobre a captura, habitat ou táticas'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data and not self.data.get('pokemon_name') and self.data.get('pokemon_number'):
            pk = find_pokemon_by_number(self.data.get('pokemon_number'))
            if pk:
                self.data = self.data.copy()
                self.data['pokemon_name'] = pk['name']

    def clean_pokemon_name(self):
        name = self.cleaned_data.get('pokemon_name', '').strip()
        if not name:
            raise forms.ValidationError('Informe o nome do Pokémon.')
        pokemon = find_pokemon_by_name(name)
        if not pokemon and name.isdigit():
            pokemon = find_pokemon_by_number(int(name))
        if not pokemon:
            raise forms.ValidationError(f"Pokémon '{name}' não foi encontrado no catálogo.")
        self.cleaned_pokemon = pokemon
        return pokemon['name']

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(self, 'cleaned_pokemon'):
            instance.pokemon_number = self.cleaned_pokemon['number']
        if commit:
            instance.save()
        return instance


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
