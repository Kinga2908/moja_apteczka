from django import forms
from .models import Lek, PrzyjecieLeku, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class LekForm(forms.ModelForm):
    class Meta:
        model = Lek
        fields = ['nazwa', 'substancja_aktywna', 'instrukcja', 'interakcje']
        widgets = {
            'nazwa': forms.TextInput(attrs={'placeholder': 'Np. Apap, Ibuprofen...'}),
            'instrukcja': forms.Textarea(attrs={'rows': 3}),
            'interakcje': forms.CheckboxSelectMultiple(),
        }
        labels = {
            'nazwa': 'Nazwa leku',
            'substancja_aktywna': 'Substancja aktywna',
            'instrukcja': 'Instrukcja przyjmowania',
            'interakcje': 'Interakcje z innymi lekami',
        }


class PrzyjęcieForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):          
        super().__init__(*args, **kwargs)
        self.fields['data_godzina'].input_formats = ['%Y-%m-%dT%H:%M']

    class Meta:
        model = PrzyjecieLeku
        fields = ['lek', 'data_godzina', 'status', 'notatka_samopoczucia']
        widgets = {
            'data_godzina': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'           
            ),
            'notatka_samopoczucia': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Jak się czujesz po leku?'}),
        }
        labels = {
            'lek': 'Lek',
            'data_godzina': 'Data i godzina przyjęcia',
            'status': 'Status',
            'notatka_samopoczucia': 'Notatka o samopoczuciu',
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['alerty_interakcji']
        labels = {
            'alerty_interakcji': 'Otrzymuj alerty o interakcjach leków',
        }


class RejestracjaForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

class ImportCSVForm(forms.Form):
    plik = forms.FileField(
        label='Plik CSV',
        help_text='Plik musi zawierać kolumny: nazwa, substancja_aktywna, instrukcja'
    )