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

    def __str__(self):
        return self.nazwa

    class Meta:
        verbose_name = "Lek"
        verbose_name_plural = "Leki"


class UserProfile(models.Model):
    uzytkownik = models.OneToOneField(User, on_delete=models.CASCADE)
    alerty_interakcji = models.BooleanField(default=True)

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