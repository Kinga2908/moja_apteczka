from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import LekForm, PrzyjęcieForm, UserProfileForm, RejestracjaForm
from .models import Lek, PrzyjecieLeku, UserProfile


def rejestracja(request):
    if request.method == 'POST':
        form = RejestracjaForm(request.POST)
        if form.is_valid():
            form.save()                    # zapisz usera
            # login(request, user)        # ← usuń tę linię
            return redirect('logowanie')  # ← przekieruj do logowania
    else:
        form = RejestracjaForm()
    return render(request, 'leki/formularz.html', {
        'form': form,
        'tytul': 'Rejestracja'
    })


def logowanie(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('strona_glowna')
    else:
        form = AuthenticationForm()
    return render(request, 'leki/formularz.html', {
        'form': form,
        'tytul': 'Logowanie'
    })


def wylogowanie(request):
    logout(request)
    return redirect('logowanie')


@login_required
def strona_glowna(request):
    from datetime import date, timedelta
    offset = int(request.GET.get('tydzien', 0)) 
    
    leki = Lek.objects.filter(uzytkownik=request.user)
    przyjecia = PrzyjecieLeku.objects.filter(uzytkownik=request.user)
    
    return render(request, 'leki/strona_glowna.html', {
        'leki': leki,
        'przyjecia': przyjecia,
        'tydzien_offset': offset,
    })


@login_required
def dodaj_lek(request):
    if request.method == 'POST':
        form = LekForm(request.POST)
        if form.is_valid():
            lek = form.save(commit=False)
            lek.uzytkownik = request.user 
            lek.save()
            form.save_m2m()              
            return redirect('strona_glowna')
    else:
        form = LekForm()
    return render(request, 'leki/formularz.html', {
        'form': form,
        'tytul': 'Dodaj nowy lek'
    })


@login_required
def dodaj_przyjecie(request):
    if request.method == 'POST':
        form = PrzyjęcieForm(request.POST)
        if form.is_valid():
            przyjecie = form.save(commit=False)
            przyjecie.uzytkownik = request.user
            przyjecie.save()
            form.save_m2m()
            return redirect('strona_glowna')
    else:
        form = PrzyjęcieForm()
    return render(request, 'leki/formularz.html', {
        'form': form,
        'tytul': 'Zarejestruj przyjęcie leku'
    })


@login_required
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

@login_required
def edytuj_przyjecie(request, pk):
    przyjecie = PrzyjecieLeku.objects.get(pk=pk, uzytkownik=request.user)
    if request.method == 'POST':
        form = PrzyjęcieForm(request.POST, instance=przyjecie)
        if form.is_valid():
            form.save()
            return redirect('strona_glowna')
    else:
        form = PrzyjęcieForm(instance=przyjecie)
    return render(request, 'leki/formularz.html', {
        'form': form,
        'tytul': 'Edytuj przyjęcie'
    })

@login_required
def zmien_status(request, pk):
    przyjecie = PrzyjecieLeku.objects.get(pk=pk, uzytkownik=request.user)
    if przyjecie.status == 'zazyte':
        przyjecie.status = 'niezazyte'
    else:
        przyjecie.status = 'zazyte'
    przyjecie.save()
    return redirect('strona_glowna')