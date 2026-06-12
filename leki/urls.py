from django.urls import path
from . import views

urlpatterns = [
    # Autentykacja
    path('rejestracja/', views.rejestracja, name='rejestracja'),
    path('logowanie/', views.logowanie, name='logowanie'),
    path('wylogowanie/', views.wylogowanie, name='wylogowanie'),
    path('profil/', views.edytuj_profil, name='edytuj_profil'),

    # Strona główna
    path('', views.strona_glowna, name='strona_glowna'),

    # Leki – lista z filtrowaniem i stronicowaniem
    path('leki/', views.lista_lekow, name='lista_lekow'),
    path('dodaj-lek/', views.dodaj_lek, name='dodaj_lek'),
    path('import-csv/', views.import_csv, name='import_csv'),
    path('skaner/', views.szukaj_po_kodzie, name='skaner'),

    # Przyjęcia – lista z filtrowaniem i stronicowaniem
    path('przyjecia/', views.lista_przyjec, name='lista_przyjec'),
    path('dodaj-przyjecie/', views.dodaj_przyjecie, name='dodaj_przyjecie'),
    path('edytuj-przyjecie/<int:pk>/', views.edytuj_przyjecie, name='edytuj_przyjecie'),
    path('zmien-status/<int:pk>/', views.zmien_status, name='zmien_status'),

    # Przypomnienia
    path('przypomnienia/', views.harmonogram_lista, name='harmonogram_lista'),
    path('przypomnienia/dodaj/', views.dodaj_harmonogram, name='dodaj_harmonogram'),
    path('przypomnienia/usun/<int:pk>/', views.usun_harmonogram, name='usun_harmonogram'),

    # Raport
    path('raport/', views.raport_miesięczny, name='raport'),
    path('raport/csv/', views.eksport_raportu_csv, name='raport_csv'),

    # Wykres PNG – dynamiczna grafika
    path('wykres/przyjecia.png', views.wykres_przyjec_png, name='wykres_przyjec_png'),

    # API dla powiadomień JS
    path('przypomnienia/api/', views.api_harmonogram, name='api_harmonogram'),
]