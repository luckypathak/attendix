import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from attendix.apps.attendance.models import Attendance, AttendanceSession

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cleanup attendance photos older than 2 days'

    def handle(self, *args, **options):
        today = timezone.localtime(timezone.now()).date()
        cutoff_date = today - timedelta(days=2)
        self.stdout.write(self.style.WARNING(f"Starting photo cleanup. Cutoff date is {cutoff_date} and older."))

        # Cleanup Attendance parent records
        parent_records = Attendance.objects.filter(date__lte=cutoff_date)
        parent_count = 0
        for att in parent_records:
            if att.captured_image:
                try:
                    att.captured_image.delete(save=True)
                    parent_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error deleting parent photo for ID {att.id}: {e}"))

        # Cleanup AttendanceSession records
        sessions = AttendanceSession.objects.filter(attendance__date__lte=cutoff_date)
        session_in_count = 0
        session_out_count = 0
        for sess in sessions:
            if sess.captured_image:
                try:
                    sess.captured_image.delete(save=True)
                    session_in_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error deleting check-in photo for session {sess.id}: {e}"))
            if sess.check_out_captured_image:
                try:
                    sess.check_out_captured_image.delete(save=True)
                    session_out_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error deleting check-out photo for session {sess.id}: {e}"))

        msg = f"Cleanup completed. Deleted {parent_count} parent photos, {session_in_count} session check-in photos, {session_out_count} session check-out photos."
        self.stdout.write(self.style.SUCCESS(msg))
        logger.info(msg)
