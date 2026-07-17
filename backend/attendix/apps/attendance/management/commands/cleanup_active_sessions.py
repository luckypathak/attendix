from django.core.management.base import BaseCommand
from django.utils import timezone
from attendix.apps.attendance.models import AttendanceSession
from attendix.apps.attendance.services import AttendanceService
from datetime import datetime, time

class Command(BaseCommand):
    help = 'Cleans up any stale active sessions where the current time is past the shift end.'

    def handle(self, *args, **options):
        self.stdout.write("Starting cleanup of stale active sessions...")
        now_dt = timezone.localtime(timezone.now())
        
        # Get active sessions without auto_checkout override, where check_out_time is null
        active_sessions = AttendanceSession.objects.filter(
            check_out_time__isnull=True,
            auto_checkout=False,
            continue_shift=False
        ).select_related('attendance__shift', 'attendance__employee')

        closed_count = 0
        
        for session in active_sessions:
            shift = session.attendance.shift
            if not shift:
                continue
                
            # Determine shift end datetime for this session
            # Since the session might have started yesterday, we need the exact date of attendance
            att_date = session.attendance.date
            
            # Reconstruct shift end datetime
            shift_end_dt = timezone.make_aware(datetime.combine(att_date, shift.end_time))
            # If shift spans midnight (e.g., ends earlier than it started)
            if shift.end_time < shift.start_time:
                from datetime import timedelta
                shift_end_dt += timedelta(days=1)
                
            if now_dt >= shift_end_dt:
                self.stdout.write(f"Closing stale session ID={session.id} for Employee {session.attendance.employee.username}")
                # Use the service auto checkout logic which will handle recalculations and logs
                # It accepts the session, now_dt, and shift_end_dt.
                # Actually, the service method 'check_active_overtimes_and_autocheckout' does exactly this,
                # but let's just trigger it or manually close it.
                # It's better to manually close to ensure no window constraints apply.
                session.check_out_time = now_dt.time()
                session.auto_checkout = True
                
                # Check for OT
                # Since this is a forced cleanup past shift end, if it's already an OT request, it shouldn't auto checkout 
                # unless explicitly allowed. But our filter continue_shift=False helps.
                if not session.ot_status or session.ot_status in ['REJECTED', 'APPROVED']:
                    # Overtime requests in PENDING remain active usually, but here we just close it
                    if session.ot_status == 'PENDING':
                        continue # wait for admin
                        
                session.save()
                
                # Recalculate metrics
                AttendanceService._recalculate_attendance_metrics(session.attendance, shift, att_date)
                
                # Log audit
                from attendix.apps.attendance.models import AttendanceAuditLog
                AttendanceAuditLog.objects.create(
                    session=session,
                    user=None, # System
                    old_value={"check_out_time": None, "auto_checkout": False},
                    new_value={"check_out_time": str(session.check_out_time), "auto_checkout": True},
                    reason="AUTO_CHECKOUT (Cleanup script)"
                )
                
                closed_count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully cleaned up {closed_count} stale sessions.'))
