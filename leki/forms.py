from django import forms
from .models import Lek, PrzyjecieLeku, UserProfile, HarmonogramPrzypomnienia
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class LekForm(forms.ModelForm):
    class Meta:
        model = Lek
        fields = ['nazwa', 'substancja_aktywna', 'instrukcja', 'interakcje',
                  'cena', 'ilosc_w_opakowaniu', 'kod_kreskowy']
        widgets = {
            'nazwa': forms.TextInput(attrs={'placeholder': 'Np. Apap, Ibuprofen...', 'class': 'form-control'}),
            'substancja_aktywna': forms.TextInput(attrs={'class': 'form-control'}),
            'instrukcja': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'interakcje': forms.CheckboxSelectMultiple(),
            'cena': forms.NumberInput(attrs={'placeholder': 'Np. 12.50', 'step': '0.01', 'class': 'form-control'}),
            'ilosc_w_opakowaniu': forms.NumberInput(attrs={'placeholder': 'Np. 20', 'class': 'form-control'}),
            'kod_kreskowy': forms.TextInput(attrs={
                'placeholder': 'Zeskanuj lub wpisz kod EAN...',
                'class': 'form-control', 'id': 'id_kod_kreskowy', 'autocomplete': 'off',
            }),
        }
        labels = {
            'nazwa': 'Nazwa leku',
            'substancja_aktywna': 'Substancja aktywna',
            'instrukcja': 'Instrukcja przyjmowania',
            'interakcje': 'Interakcje z innymi lekami',
            'cena': 'Cena opakowania (zł)',
            'ilosc_w_opakowaniu': 'Liczba dawek w opakowaniu',
            'kod_kreskowy': 'Kod kreskowy (EAN)',
        }


class PrzyjęcieForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['data_godzina'].input_formats = ['%Y-%m-%dT%H:%M']
        if user:
            self.fields['lek'].queryset = Lek.objects.filter(uzytkownik=user)

    class Meta:
        model = PrzyjecieLeku
        fields = ['lek', 'data_godzina', 'status', 'notatka_samopoczucia']
        widgets = {
            'data_godzina': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'notatka_samopoczucia': forms.Textarea(attrs={
                'rows': 3, 'placeholder': 'Jak się czujesz po leku?', 'class': 'form-control'
            }),
            'lek': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'lek': 'Lek', 'data_godzina': 'Data i godzina przyjęcia',
            'status': 'Status', 'notatka_samopoczucia': 'Notatka o samopoczuciu',
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['alerty_interakcji', 'email_powiadomien']
        labels = {
            'alerty_interakcji': 'Otrzymuj alerty o interakcjach leków',
            'email_powiadomien': 'E-mail do przypomnień (opcjonalnie)',
        }
        widgets = {
            'email_powiadomien': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'twoj@email.com'
            }),
        }


class RejestracjaForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

<<<<<<< HEAD

class ImportCSVForm(forms.Form):
    plik_csv = forms.FileField(
        label="Plik CSV z lekami",
        help_text="Wymagane kolumny: nazwa, substancja_aktywna, instrukcja. Opcjonalne: cena, ilosc_w_opakowaniu, kod_kreskowy.",
        widget=forms.FileInput(attrs={'accept': '.csv', 'class': 'form-control'})
    )


class HarmonogramForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['lek'].queryset = Lek.objects.filter(uzytkownik=user)

    class Meta:
        model = HarmonogramPrzypomnienia
        fields = ['lek', 'godzina', 'aktywne']
        widgets = {
            'lek': forms.Select(attrs={'class': 'form-control'}),
            'godzina': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
        labels = {'lek': 'Lek', 'godzina': 'Godzina przypomnienia', 'aktywne': 'Aktywne'}


class RaportForm(forms.Form):
    ROK_CHOICES = [(r, str(r)) for r in range(2024, 2028)]
    MIESIAC_CHOICES = [
        (1,'Styczeń'),(2,'Luty'),(3,'Marzec'),(4,'Kwiecień'),
        (5,'Maj'),(6,'Czerwiec'),(7,'Lipiec'),(8,'Sierpień'),
        (9,'Wrzesień'),(10,'Październik'),(11,'Listopad'),(12,'Grudzień'),
    ]
    rok = forms.ChoiceField(choices=ROK_CHOICES, label='Rok',
                            widget=forms.Select(attrs={'class': 'form-control'}))
    miesiac = forms.ChoiceField(choices=MIESIAC_CHOICES, label='Miesiąc',
                                widget=forms.Select(attrs={'class': 'form-control'}))


# ── NOWE: Formularze filtrowania ───────────────────────────────────────────────

class FiltrLekiForm(forms.Form):
    """Filtrowanie listy leków – pola tekstowe i liczbowe."""
    nazwa = forms.CharField(
        required=False, label='Nazwa leku',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Szukaj nazwy...'})
    )
    substancja = forms.CharField(
        required=False, label='Substancja aktywna',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Szukaj substancji...'})
    )
    cena_min = forms.DecimalField(
        required=False, label='Cena od (zł)', min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'})
    )
    cena_max = forms.DecimalField(
        required=False, label='Cena do (zł)', min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '999.99', 'step': '0.01'})
    )
    kod_kreskowy = forms.CharField(
        required=False, label='Kod kreskowy',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'EAN...'})
    )


class FiltrPrzyjeciaForm(forms.Form):
    """Filtrowanie listy przyjęć – pola: lek (select), status, daty, notatka."""
    STATUS_CHOICES = [('', '-- wszystkie --'), ('zazyte', 'Zażyte'), ('niezazyte', 'Niezażyte')]

    lek = forms.ModelChoiceField(
        queryset=Lek.objects.none(), required=False, label='Lek',
        empty_label='-- wszystkie --',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES, required=False, label='Status',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    data_od = forms.DateField(
        required=False, label='Data od',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    data_do = forms.DateField(
        required=False, label='Data do',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    notatka = forms.CharField(
        required=False, label='Szukaj w notatkach',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Słowo kluczowe...'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['lek'].queryset = Lek.objects.filter(uzytkownik=user)
=======
class ImportCSVForm(forms.Form):
    plik = forms.FileField(
        label='Plik CSV',
        help_text='Plik musi zawierać kolumny: nazwa, substancja_aktywna, instrukcja'
    )
>>>>>>> d96afb8801182f615df8a8b0e22585a72c05cfe6
