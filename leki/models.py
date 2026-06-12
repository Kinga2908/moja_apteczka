from django.db import models
from django.contrib.auth.models import User


class Lek(models.Model):
    nazwa = models.CharField(max_length=200)
    substancja_aktywna = models.CharField(max_length=200)
    instrukcja = models.TextField(help_text="Dawkowanie, pora dnia, z czym nie łączyć")
    interakcje = models.ManyToManyField(
        'self',
        blank=True,
        verbose_name="Interakcje z innymi lekami"
    )
    uzytkownik = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leki',
        null=True
    )

    # ── NOWE POLA ──────────────────────────────────────────────────────────────
    cena = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name="Cena opakowania (zł)",
        help_text="Cena jednego opakowania w złotych"
    )
    ilosc_w_opakowaniu = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Liczba tabletek / dawek w opakowaniu",
        help_text="Np. 20 tabletek, 30 kapsułek"
    )
    kod_kreskowy = models.CharField(
        max_length=30, blank=True,
        verbose_name="Kod kreskowy (EAN)",
        help_text="Wpisz lub zeskanuj kod z opakowania"
    )
    # ──────────────────────────────────────────────────────────────────────────

    def __str__(self):
        return self.nazwa

    @property
    def cena_za_dawke(self):
        """Koszt pojedynczej dawki."""
        if self.cena and self.ilosc_w_opakowaniu:
            return round(self.cena / self.ilosc_w_opakowaniu, 4)
        return None

    class Meta:
        verbose_name = "Lek"
        verbose_name_plural = "Leki"


class UserProfile(models.Model):
    uzytkownik = models.OneToOneField(User, on_delete=models.CASCADE)
    alerty_interakcji = models.BooleanField(default=True)
    # NOWE: e-mail do przypomnień (może być inny niż konto)
    email_powiadomien = models.EmailField(
        blank=True,
        verbose_name="E-mail do przypomnień",
        help_text="Zostaw puste, aby używać e-maila konta"
    )

    def __str__(self):
        return f"Profil: {self.uzytkownik.username}"

    class Meta:
        verbose_name = "Profil użytkownika"


class PrzyjecieLeku(models.Model):
    STATUS_CHOICES = [
        ('zazyte', 'Zażyte'),
        ('niezazyte', 'Niezażyte'),
    ]
    lek = models.ForeignKey(Lek, on_delete=models.CASCADE, related_name='przyjecia')
    uzytkownik = models.ForeignKey(User, on_delete=models.CASCADE, related_name='przyjecia')
    data_godzina = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='niezazyte')
    notatka_samopoczucia = models.TextField(blank=True)

    def __str__(self):
        return f"{self.lek.nazwa} — {self.uzytkownik.username} — {self.data_godzina}"

    class Meta:
        verbose_name = "Przyjęcie leku"
        verbose_name_plural = "Przyjęcia leków"
        ordering = ['-data_godzina']


# ── NOWY MODEL: harmonogram przypomnień ────────────────────────────────────────
class HarmonogramPrzypomnienia(models.Model):
    """
    Definiuje, kiedy użytkownik chce dostawać przypomnienie o danym leku.
    Jedna para lek+godzina = jeden wiersz.
    """
    GODZINY_CHOICES = [(f"{h:02d}:00", f"{h:02d}:00") for h in range(6, 23)]

    uzytkownik = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='harmonogramy'
    )
    lek = models.ForeignKey(
        Lek, on_delete=models.CASCADE,
        related_name='harmonogramy',
        verbose_name="Lek"
    )
    godzina = models.TimeField(
        verbose_name="Godzina przypomnienia",
        help_text="Format HH:MM, np. 08:00"
    )
    aktywne = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.lek.nazwa} – {self.godzina} ({self.uzytkownik.username})"

    class Meta:
        verbose_name = "Harmonogram przypomnienia"
        verbose_name_plural = "Harmonogramy przypomnień"
        ordering = ['godzina']
# ──────────────────────────────────────────────────────────────────────────────