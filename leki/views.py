from django.shortcuts import render, redirect
from .forms import LekForm, PrzyjęcieForm, UserProfileForm
from .models import Lek, PrzyjecieLeku

def strona_glowna(request):
    leki = Lek.objects.all()
    przyjecia = PrzyjecieLeku.objects.all()
    return render(request, 'leki/strona_glowna.html', {
        'leki': leki,
        'przyjecia': przyjecia
    })

def dodaj_lek(request):
    if request.method == 'POST':
        form = LekForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('strona_glowna')
    else:
        form = LekForm()
    return render(request, 'leki/formularz.html', {
        'form': form,
        'tytul': 'Dodaj nowy lek'
    })

def dodaj_przyjecie(request):
    if request.method == 'POST':
        form = PrzyjęcieForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('strona_glowna')
    else:
        form = PrzyjęcieForm()
    return render(request, 'leki/formularz.html', {
        'form': form,
        'tytul': 'Zarejestruj przyjęcie leku'
    })

def edytuj_profil(request):
    profil, created = UserProfile.objects.get_or_create(uzytkownik=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profil)
        if form.is_valid():
            form.save()
            return redirect('strona_glowna')
    else:
        form = UserProfileForm(instance=profil)
    return render(request, 'leki/formularz.html', {
        'form': form,
        'tytul': 'Edytuj profil'
    })