"""
management/commands/wyslij_przypomnienia.py

Komenda Django do wysyłania codziennych przypomnień o lekach.

UŻYCIE:
    python manage.py wyslij_przypomnienia

CRON (co 15 minut, sprawdza czy jest czas przypomnienia):
    */15 * * * * cd /sciezka/do/projektu && python manage.py wyslij_przypomnienia

USTAWIENIA w settings.py:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'twoj@gmail.com'
    EMAIL_HOST_PASSWORD = 'haslo_aplikacji'   # hasło aplikacji Google
    DEFAULT_FROM_EMAIL = 'MediMate <twoj@gmail.com>'

TESTOWANIE (bez prawdziwego SMTP):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    → e-maile pojawią się w terminalu zamiast być wysyłane
"""

from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from leki.models import HarmonogramPrzypomnienia


class Command(BaseCommand):
    help = 'Wysyła e-mailowe przypomnienia o lekach na podstawie harmonogramu.'

    def handle(self, *args, **options):
        teraz = datetime.now()
        # Okno czasowe: ±7 minut od pełnej godziny ustawionej w harmonogramie
        okno_start = (teraz - timedelta(minutes=7)).time().replace(second=0, microsecond=0)
        okno_stop = (teraz + timedelta(minutes=7)).time().replace(second=0, microsecond=0)

        harmonogramy = HarmonogramPrzypomnienia.objects.filter(
            aktywne=True,
            godzina__gte=okno_start,
            godzina__lte=okno_stop,
        ).select_related('uzytkownik', 'uzytkownik__userprofile', 'lek')

        wyslano = 0
        for h in harmonogramy:
            user = h.uzytkownik
            try:
                profil = user.userprofile
                email = profil.email_powiadomien or user.email
            except Exception:
                email = user.email

            if not email:
                self.stdout.write(
                    self.style.WARNING(
                        f'Brak e-maila dla {user.username} – pominięto przypomnienie o {h.lek.nazwa}'
                    )
                )
                continue

            temat = f'💊 MediMate – czas na {h.lek.nazwa}'
            tresc = (
                f'Cześć {user.username}!\n\n'
                f'Przypominamy, że o godzinie {h.godzina.strftime("%H:%M")} '
                f'powinieneś/-aś przyjąć lek:\n\n'
                f'  🔹 {h.lek.nazwa} ({h.lek.substancja_aktywna})\n'
                f'  📋 {h.lek.instrukcja}\n\n'
                f'Zaloguj się do MediMate, aby potwierdzić przyjęcie.\n\n'
                f'Pozdrawiamy,\nZespół MediMate'
            )

            try:
                send_mail(
                    subject=temat,
                    message=tresc,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                wyslano += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Wysłano do {email} ({h.lek.nazwa})'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Błąd wysyłki do {email}: {e}')
                )

        self.stdout.write(f'\nWysłano {wyslano} przypomnień.')
