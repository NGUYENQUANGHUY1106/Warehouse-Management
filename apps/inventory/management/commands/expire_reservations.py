from django.core.management.base import BaseCommand

from apps.inventory.services import release_expired_reservations


class Command(BaseCommand):
    help = "Nhả các phiên giữ tồn kho đã quá hạn."

    def handle(self, *args, **options):
        count = release_expired_reservations()
        self.stdout.write(self.style.SUCCESS(f"Released {count} expired reservations."))
