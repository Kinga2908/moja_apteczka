import csv
import io
import base64
from decimal import Decimal, InvalidOperation
from datetime import date, timedelta
from calendar import monthrange
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator

from .forms import (
    LekForm, PrzyjęcieForm, UserProfileForm, RejestracjaForm,
    ImportCSVForm, HarmonogramForm, RaportForm, FiltrLekiForm, FiltrPrzyjeciaForm,
)
from .models import Lek, PrzyjecieLeku, UserProfile, HarmonogramPrzypomnienia


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTENTYKACJA
# ═══════════════════════════════════════════════════════════════════════════════

def rejestracja(request):
    if request.method == 'POST':
        form = RejestracjaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('logowanie')
    else:
        form = RejestracjaForm()
    return render(request, 'leki/formularz.html', {'form': form, 'tytul': 'Rejestracja'})


def logowanie(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('strona_glowna')
    else:
        form = AuthenticationForm()
    return render(request, 'leki/formularz.html', {'form': form, 'tytul': 'Logowanie'})


def wylogowanie(request):
    logout(request)
    return redirect('logowanie')


# ═══════════════════════════════════════════════════════════════════════════════
#  STRONA GŁÓWNA
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def strona_glowna(request):
    offset = int(request.GET.get('tydzien', 0))
    leki = Lek.objects.filter(uzytkownik=request.user)
    przyjecia = PrzyjecieLeku.objects.filter(uzytkownik=request.user)

    dzis = date.today()
    poniedzialek = dzis - timedelta(days=dzis.weekday())
    niedziela = poniedzialek + timedelta(days=6)

    przyjecia_tydzien = PrzyjecieLeku.objects.filter(
        uzytkownik=request.user,
        status='zazyte',
        data_godzina__date__gte=poniedzialek,
        data_godzina__date__lte=niedziela,
    ).select_related('lek')

    koszt_tygodnia = Decimal('0.00')
    for p in przyjecia_tydzien:
        if p.lek.cena_za_dawke:
            koszt_tygodnia += Decimal(str(p.lek.cena_za_dawke))

    return render(request, 'leki/strona_glowna.html', {
        'leki': leki,
        'przyjecia': przyjecia,
        'tydzien_offset': offset,
        'koszt_tygodnia': koszt_tygodnia,
        'tydzien_od': poniedzialek,
        'tydzien_do': niedziela,
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  LISTA LEKÓW ze stronicowaniem i filtrowaniem
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def lista_lekow(request):
    """Lista leków z filtrowaniem (nazwa, substancja, cena min/max) i stronicowaniem."""
    qs = Lek.objects.filter(uzytkownik=request.user)

    form = FiltrLekiForm(request.GET or None)
    if form.is_valid():
        nazwa = form.cleaned_data.get('nazwa')
        substancja = form.cleaned_data.get('substancja')
        cena_min = form.cleaned_data.get('cena_min')
        cena_max = form.cleaned_data.get('cena_max')
        kod = form.cleaned_data.get('kod_kreskowy')

        if nazwa:
            qs = qs.filter(nazwa__icontains=nazwa)
        if substancja:
            qs = qs.filter(substancja_aktywna__icontains=substancja)
        if cena_min is not None:
            qs = qs.filter(cena__gte=cena_min)
        if cena_max is not None:
            qs = qs.filter(cena__lte=cena_max)
        if kod:
            qs = qs.filter(kod_kreskowy__icontains=kod)

    # Stronicowanie
    wyniki_na_stronie = request.GET.get('na_stronie', '10')
    try:
        wyniki_na_stronie = int(wyniki_na_stronie)
        if wyniki_na_stronie not in [5, 10, 25, 50]:
            wyniki_na_stronie = 10
    except ValueError:
        wyniki_na_stronie = 10

    paginator = Paginator(qs, wyniki_na_stronie)
    strona = request.GET.get('strona', 1)
    try:
        leki_strona = paginator.page(strona)
    except Exception:
        leki_strona = paginator.page(1)

    # Zachowaj parametry GET bez 'strona' do linków paginacji
    get_params = request.GET.copy()
    get_params.pop('strona', None)

    return render(request, 'leki/lista_lekow.html', {
        'leki': leki_strona,
        'form': form,
        'paginator': paginator,
        'wyniki_na_stronie': wyniki_na_stronie,
        'get_params': get_params.urlencode(),
        'opcje_na_stronie': [5, 10, 25, 50],
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  LISTA PRZYJĘĆ ze stronicowaniem i filtrowaniem
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def lista_przyjec(request):
    """Lista przyjęć z filtrowaniem (lek, status, data od/do) i stronicowaniem."""
    qs = PrzyjecieLeku.objects.filter(uzytkownik=request.user).select_related('lek')

    form = FiltrPrzyjeciaForm(request.GET or None, user=request.user)
    if form.is_valid():
        lek = form.cleaned_data.get('lek')
        status = form.cleaned_data.get('status')
        data_od = form.cleaned_data.get('data_od')
        data_do = form.cleaned_data.get('data_do')
        notatka = form.cleaned_data.get('notatka')

        if lek:
            qs = qs.filter(lek=lek)
        if status:
            qs = qs.filter(status=status)
        if data_od:
            qs = qs.filter(data_godzina__date__gte=data_od)
        if data_do:
            qs = qs.filter(data_godzina__date__lte=data_do)
        if notatka:
            qs = qs.filter(notatka_samopoczucia__icontains=notatka)

    wyniki_na_stronie = request.GET.get('na_stronie', '10')
    try:
        wyniki_na_stronie = int(wyniki_na_stronie)
        if wyniki_na_stronie not in [5, 10, 25, 50]:
            wyniki_na_stronie = 10
    except ValueError:
        wyniki_na_stronie = 10

    paginator = Paginator(qs, wyniki_na_stronie)
    strona = request.GET.get('strona', 1)
    try:
        przyjecia_strona = paginator.page(strona)
    except Exception:
        przyjecia_strona = paginator.page(1)

    get_params = request.GET.copy()
    get_params.pop('strona', None)

    return render(request, 'leki/lista_przyjec.html', {
        'przyjecia': przyjecia_strona,
        'form': form,
        'paginator': paginator,
        'wyniki_na_stronie': wyniki_na_stronie,
        'get_params': get_params.urlencode(),
        'opcje_na_stronie': [5, 10, 25, 50],
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  LEKI – CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def dodaj_lek(request):
    if request.method == 'POST':
        form = LekForm(request.POST)
        if form.is_valid():
            lek = form.save(commit=False)
            lek.uzytkownik = request.user
            lek.save()
            form.save_m2m()
            messages.success(request, f'Lek „{lek.nazwa}" został dodany.')
            return redirect('lista_lekow')
    else:
        kod = request.GET.get('kod', '')
        form = LekForm(initial={'kod_kreskowy': kod})
    return render(request, 'leki/dodaj_lek.html', {'form': form, 'tytul': 'Dodaj nowy lek'})


@login_required
def szukaj_po_kodzie(request):
    kod = request.GET.get('kod', '').strip()
    lek_znaleziony = None
    if kod:
        lek_znaleziony = Lek.objects.filter(
            uzytkownik=request.user, kod_kreskowy=kod
        ).first()
    return render(request, 'leki/skaner.html', {
        'kod': kod,
        'lek': lek_znaleziony,
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  PRZYJĘCIA
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def dodaj_przyjecie(request):
    if request.method == 'POST':
        form = PrzyjęcieForm(request.POST, user=request.user)
        if form.is_valid():
            przyjecie = form.save(commit=False)
            przyjecie.uzytkownik = request.user
            przyjecie.save()
            return redirect('lista_przyjec')
    else:
        form = PrzyjęcieForm(user=request.user)
    return render(request, 'leki/formularz.html', {
        'form': form, 'tytul': 'Zarejestruj przyjęcie leku'
    })


@login_required
def edytuj_przyjecie(request, pk):
    przyjecie = get_object_or_404(PrzyjecieLeku, pk=pk, uzytkownik=request.user)
    if request.method == 'POST':
        form = PrzyjęcieForm(request.POST, instance=przyjecie, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('lista_przyjec')
    else:
        form = PrzyjęcieForm(instance=przyjecie, user=request.user)
    return render(request, 'leki/formularz.html', {'form': form, 'tytul': 'Edytuj przyjęcie'})


@login_required
def zmien_status(request, pk):
    przyjecie = get_object_or_404(PrzyjecieLeku, pk=pk, uzytkownik=request.user)
    przyjecie.status = 'niezazyte' if przyjecie.status == 'zazyte' else 'zazyte'
    przyjecie.save()
    # Wróć do poprzedniej strony
    return redirect(request.META.get('HTTP_REFERER', 'lista_przyjec'))


# ═══════════════════════════════════════════════════════════════════════════════
#  PROFIL
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def edytuj_profil(request):
    profil, _ = UserProfile.objects.get_or_create(uzytkownik=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profil)
        if form.is_valid():
            form.save()
            return redirect('strona_glowna')
    else:
        form = UserProfileForm(instance=profil)
    return render(request, 'leki/formularz.html', {'form': form, 'tytul': 'Edytuj profil'})


# ═══════════════════════════════════════════════════════════════════════════════
#  IMPORT CSV
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def import_csv(request):
    if request.method == 'POST':
        form = ImportCSVForm(request.POST, request.FILES)
        if form.is_valid():
            plik = request.FILES['plik_csv']
            try:
                tresc = plik.read().decode('utf-8-sig')
            except UnicodeDecodeError:
                tresc = plik.read().decode('latin-2')

            reader = csv.DictReader(io.StringIO(tresc))
            wymagane = {'nazwa', 'substancja_aktywna', 'instrukcja'}
            if not wymagane.issubset(set(reader.fieldnames or [])):
                messages.error(request,
                    f'Brak wymaganych kolumn. Plik musi zawierać: {", ".join(wymagane)}')
                return render(request, 'leki/import_csv.html', {'form': form})

            dodano = 0
            bledy = []
            for i, row in enumerate(reader, start=2):
                nazwa = row.get('nazwa', '').strip()
                if not nazwa:
                    bledy.append(f'Wiersz {i}: brak nazwy – pominięto.')
                    continue
                if Lek.objects.filter(uzytkownik=request.user, nazwa__iexact=nazwa).exists():
                    bledy.append(f'Wiersz {i}: „{nazwa}" już istnieje – pominięto.')
                    continue
                cena = None
                try:
                    raw_cena = row.get('cena', '').strip().replace(',', '.')
                    if raw_cena:
                        cena = Decimal(raw_cena)
                except InvalidOperation:
                    bledy.append(f'Wiersz {i}: nieprawidłowa cena – ustawiono brak.')
                ilosc = None
                try:
                    raw_ilosc = row.get('ilosc_w_opakowaniu', '').strip()
                    if raw_ilosc:
                        ilosc = int(raw_ilosc)
                except ValueError:
                    pass
                Lek.objects.create(
                    nazwa=nazwa,
                    substancja_aktywna=row.get('substancja_aktywna', '').strip(),
                    instrukcja=row.get('instrukcja', '').strip(),
                    cena=cena,
                    ilosc_w_opakowaniu=ilosc,
                    kod_kreskowy=row.get('kod_kreskowy', '').strip(),
                    uzytkownik=request.user,
                )
                dodano += 1

            if dodano:
                messages.success(request, f'Zaimportowano {dodano} leków.')
            for b in bledy:
                messages.warning(request, b)
            return redirect('lista_lekow')
    else:
        form = ImportCSVForm()
    return render(request, 'leki/import_csv.html', {'form': form})


# ═══════════════════════════════════════════════════════════════════════════════
#  HARMONOGRAM PRZYPOMNIEŃ
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def harmonogram_lista(request):
    harmonogramy = HarmonogramPrzypomnienia.objects.filter(
        uzytkownik=request.user
    ).select_related('lek')
    return render(request, 'leki/harmonogram_lista.html', {'harmonogramy': harmonogramy})


@login_required
def dodaj_harmonogram(request):
    if request.method == 'POST':
        form = HarmonogramForm(request.POST, user=request.user)
        if form.is_valid():
            h = form.save(commit=False)
            h.uzytkownik = request.user
            h.save()
            messages.success(request, 'Przypomnienie zostało dodane.')
            return redirect('harmonogram_lista')
    else:
        form = HarmonogramForm(user=request.user)
    return render(request, 'leki/formularz.html', {
        'form': form, 'tytul': 'Dodaj przypomnienie o leku'
    })


@login_required
def usun_harmonogram(request, pk):
    h = get_object_or_404(HarmonogramPrzypomnienia, pk=pk, uzytkownik=request.user)
    h.delete()
    messages.success(request, 'Przypomnienie zostało usunięte.')
    return redirect('harmonogram_lista')


# ═══════════════════════════════════════════════════════════════════════════════
#  RAPORT MIESIĘCZNY
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def raport_miesięczny(request):
    dzis = date.today()
    rok = int(request.GET.get('rok', dzis.year))
    miesiac = int(request.GET.get('miesiac', dzis.month))

    form = RaportForm(initial={'rok': rok, 'miesiac': miesiac})
    pierwszy_dzien = date(rok, miesiac, 1)
    ostatni_dzien = date(rok, miesiac, monthrange(rok, miesiac)[1])

    przyjecia_qs = PrzyjecieLeku.objects.filter(
        uzytkownik=request.user,
        data_godzina__date__gte=pierwszy_dzien,
        data_godzina__date__lte=ostatni_dzien,
    ).select_related('lek')

    total = przyjecia_qs.count()
    zazyte = przyjecia_qs.filter(status='zazyte').count()
    niezazyte = przyjecia_qs.filter(status='niezazyte').count()
    procent_przyjec = round(zazyte / total * 100, 1) if total else 0

    koszt_total = Decimal('0.00')
    for p in przyjecia_qs.filter(status='zazyte'):
        if p.lek.cena_za_dawke:
            koszt_total += Decimal(str(p.lek.cena_za_dawke))

    per_lek = defaultdict(lambda: {'zazyte': 0, 'niezazyte': 0, 'koszt': Decimal('0.00')})
    for p in przyjecia_qs:
        per_lek[p.lek.nazwa][p.status] += 1
        if p.status == 'zazyte' and p.lek.cena_za_dawke:
            per_lek[p.lek.nazwa]['koszt'] += Decimal(str(p.lek.cena_za_dawke))

    z_notatkami = przyjecia_qs.exclude(notatka_samopoczucia='').values(
        'lek__nazwa', 'data_godzina', 'notatka_samopoczucia'
    )

    leki_uzytkownika = Lek.objects.filter(uzytkownik=request.user).prefetch_related('interakcje')
    interakcje_lista = []
    for lek in leki_uzytkownika:
        for inter in lek.interakcje.all():
            interakcje_lista.append((lek.nazwa, inter.nazwa))
    interakcje_unikalne = list({tuple(sorted(p)) for p in interakcje_lista})

    nazwa_miesiaca = dict(RaportForm.MIESIAC_CHOICES)[miesiac]

    return render(request, 'leki/raport.html', {
        'form': form,
        'rok': rok,
        'miesiac': miesiac,
        'nazwa_miesiaca': nazwa_miesiaca,
        'total': total,
        'zazyte': zazyte,
        'niezazyte': niezazyte,
        'procent_przyjec': procent_przyjec,
        'koszt_total': koszt_total,
        'per_lek': dict(per_lek),
        'z_notatkami': z_notatkami,
        'interakcje_unikalne': interakcje_unikalne,
    })


@login_required
def eksport_raportu_csv(request):
    dzis = date.today()
    rok = int(request.GET.get('rok', dzis.year))
    miesiac = int(request.GET.get('miesiac', dzis.month))
    pierwszy_dzien = date(rok, miesiac, 1)
    ostatni_dzien = date(rok, miesiac, monthrange(rok, miesiac)[1])

    przyjecia_qs = PrzyjecieLeku.objects.filter(
        uzytkownik=request.user,
        data_godzina__date__gte=pierwszy_dzien,
        data_godzina__date__lte=ostatni_dzien,
    ).select_related('lek').order_by('data_godzina')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="raport_{rok}_{miesiac:02d}.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['Data i godzina', 'Lek', 'Status', 'Notatka', 'Koszt dawki (zł)'])
    for p in przyjecia_qs:
        writer.writerow([
            p.data_godzina.strftime('%Y-%m-%d %H:%M'),
            p.lek.nazwa,
            p.get_status_display(),
            p.notatka_samopoczucia,
            str(p.lek.cena_za_dawke or ''),
        ])
    return response


# ═══════════════════════════════════════════════════════════════════════════════
#  WYKRES MATPLOTLIB – widok serwujący PNG
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def wykres_przyjec_png(request):
    """
    Zwraca dynamiczny wykres słupkowy przyjęć z ostatnich 30 dni jako obraz PNG.
    To jest dedykowany widok serwujący grafikę — spełnia wymóg 'dynamiczna grafika'.
    """
    dzis = date.today()
    rok = int(request.GET.get('rok', dzis.year))
    miesiac = int(request.GET.get('miesiac', dzis.month))
    pierwszy_dzien = date(rok, miesiac, 1)
    ostatni_dzien = date(rok, miesiac, monthrange(rok, miesiac)[1])

    przyjecia_qs = PrzyjecieLeku.objects.filter(
        uzytkownik=request.user,
        data_godzina__date__gte=pierwszy_dzien,
        data_godzina__date__lte=ostatni_dzien,
    ).select_related('lek')

    # Zbierz dane per lek
    per_lek = defaultdict(lambda: {'zazyte': 0, 'niezazyte': 0})
    for p in przyjecia_qs:
        per_lek[p.lek.nazwa][p.status] += 1

    if not per_lek:
        # Pusty wykres z komunikatem
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, 'Brak danych dla wybranego okresu',
                ha='center', va='center', fontsize=14, color='gray',
                transform=ax.transAxes)
        ax.set_axis_off()
    else:
        nazwy = list(per_lek.keys())
        zazyte_vals = [per_lek[n]['zazyte'] for n in nazwy]
        niezazyte_vals = [per_lek[n]['niezazyte'] for n in nazwy]

        x = range(len(nazwy))
        fig, ax = plt.subplots(figsize=(max(8, len(nazwy) * 1.5), 5))
        szerokosc = 0.35

        slupki1 = ax.bar([i - szerokosc/2 for i in x], zazyte_vals,
                         szerokosc, label='Zażyte', color='#2c7a4b', alpha=0.85)
        slupki2 = ax.bar([i + szerokosc/2 for i in x], niezazyte_vals,
                         szerokosc, label='Niezażyte', color='#e0a800', alpha=0.85)

        # Wartości nad słupkami
        for slupek in slupki1:
            h = slupek.get_height()
            if h > 0:
                ax.annotate(str(int(h)),
                    xy=(slupek.get_x() + slupek.get_width() / 2, h),
                    xytext=(0, 3), textcoords='offset points',
                    ha='center', va='bottom', fontsize=9)
        for slupek in slupki2:
            h = slupek.get_height()
            if h > 0:
                ax.annotate(str(int(h)),
                    xy=(slupek.get_x() + slupek.get_width() / 2, h),
                    xytext=(0, 3), textcoords='offset points',
                    ha='center', va='bottom', fontsize=9)

        miesiac_nazwa = {1:'Styczeń',2:'Luty',3:'Marzec',4:'Kwiecień',5:'Maj',
                         6:'Czerwiec',7:'Lipiec',8:'Sierpień',9:'Wrzesień',
                         10:'Październik',11:'Listopad',12:'Grudzień'}

        ax.set_title(f'Przyjęcia leków – {miesiac_nazwa.get(miesiac,"")} {rok}',
                     fontsize=14, fontweight='bold', color='#2c7a4b', pad=15)
        ax.set_xticks(list(x))
        ax.set_xticklabels(nazwy, rotation=20, ha='right', fontsize=10)
        ax.set_ylabel('Liczba dawek', fontsize=11)
        ax.set_ylim(0, max(max(zazyte_vals), max(niezazyte_vals), 1) + 2)
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        fig.patch.set_facecolor('#f8f9fa')
        ax.set_facecolor('#f8f9fa')

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


# ═══════════════════════════════════════════════════════════════════════════════
#  API – harmonogram dla powiadomień JS
# ═══════════════════════════════════════════════════════════════════════════════

from django.http import JsonResponse

@login_required
def api_harmonogram(request):
    """Zwraca harmonogram przypomnień jako JSON dla powiadomień na stronie."""
    harmonogramy = HarmonogramPrzypomnienia.objects.filter(
        uzytkownik=request.user,
        aktywne=True
    ).select_related('lek')

    dane = [
        {
            'id': h.pk,
            'lek_nazwa': h.lek.nazwa,
            'godzina': h.godzina.strftime('%H:%M'),
        }
        for h in harmonogramy
    ]
    return JsonResponse({'harmonogramy': dane})