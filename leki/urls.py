from django.urls import path
from . import views

urlpatterns = [
    path('', views.strona_glowna, name='strona_glowna'),
    path('dodaj-lek/', views.dodaj_lek, name='dodaj_lek'),
    path('dodaj-przyjecie/', views.dodaj_przyjecie, name='dodaj_przyjecie'),
    path('profil/', views.edytuj_profil, name='edytuj_profil'),
    path('rejestracja/', views.rejestracja, name='rejestracja'),
    path('logowanie/', views.logowanie, name='logowanie'),
    path('wylogowanie/', views.wylogowanie, name='wylogowanie'),
    path('edytuj-przyjecie/<int:pk>/', views.edytuj_przyjecie, name='edytuj_przyjecie'),
    path('zmien-status/<int:pk>/', views.zmien_status, name='zmien_status'),
]