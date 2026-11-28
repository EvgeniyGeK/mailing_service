from django.core.management.base import BaseCommand
from django.utils import timezone
from mailing.models import Mailing
from mailing.services import send_mailing


class Command(BaseCommand):
    help = 'Запускает отправку всех актуальных рассылок'

    def handle(self, *args, **options):
        now = timezone.now()
        active_mailings = Mailing.objects.filter(start_time__lte=now, end_time__gte=now)

        if not active_mailings.exists():
            self.stdout.write(self.style.WARNING('Нет активных рассылок для отправки.'))
            return

        for mailing in active_mailings:
            success, message = send_mailing(mailing)
            if success:
                self.stdout.write(self.style.SUCCESS(f'Рассылка #{mailing.pk}: {message}'))
            else:
                self.stdout.write(self.style.ERROR(f'Рассылка #{mailing.pk}: {message}'))
