from django import forms
from .models import Lek, PrzyjecieLeku, UserProfile

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
    class Meta:
        model = PrzyjecieLeku
        fields = ['lek', 'data_godzina', 'status', 'notatka_samopoczucia']
        widgets = {
            'data_godzina': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
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