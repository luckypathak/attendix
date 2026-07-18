from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from attendix.apps.attendance.models import AttendanceSession
from attendix.apps.notifications.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Generates notifications for yesterday\'s missed checkouts.'

    def handle(self, *args, **kwargs):
        yesterday = timezone.localtime(timezone.now()).date() - timedelta(days=1)
        
        # Get all sessions from yesterday that were auto-checked out
        missed = AttendanceSession.objects.filter(
            attendance__date=yesterday,
            auto_checkout=True
        ).select_related('attendance__employee')
        
        if not missed.exists():
            self.stdout.write("No missed checkouts yesterday.")
            return

        admins = User.objects.filter(role__in=['SUPER_ADMIN', 'COMPANY_ADMIN'])
        
        for session in missed:
            emp = session.attendance.employee
            message = f"Yesterday Missed Checkout: {emp.username} - Auto Checked Out"
            for admin in admins:
                # Check if notification already exists to prevent duplicates
                exists = Notification.objects.filter(
                    recipient=admin,
                    title="Missed Checkout",
                    body=message,
                    created_at__date=timezone.localtime(timezone.now()).date()
                ).exists()
                if not exists:
                    Notification.objects.create(
                        recipient=admin,
                        title="Missed Checkout",
                        body=message,
                        notification_type="IN_APP",
                        status="PENDING"
                    )
        
        self.stdout.write(f"Generated notifications for {missed.count()} missed checkouts.")
