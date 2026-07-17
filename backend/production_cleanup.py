import os
import sys
import django

sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from django.utils import timezone
from datetime import datetime, timedelta
from attendix.apps.attendance.models import AttendanceSession, Overtime, AttendanceAuditLog
from attendix.apps.attendance.services import AttendanceService

def cleanup():
    now_dt = timezone.localtime(timezone.now())
    active_sessions = AttendanceSession.objects.filter(
        check_out_time__isnull=True,
        auto_checkout=False
    ).select_related('attendance__shift', 'attendance__employee')

    count = 0
    for session in active_sessions:
        shift = session.attendance.shift
        if not shift:
            continue
            
        att_date = session.attendance.date
        shift_end_dt = timezone.make_aware(datetime.combine(att_date, shift.end_time))
        if shift.end_time < shift.start_time:
            shift_end_dt += timedelta(days=1)
            
        grace_period_end = shift_end_dt + timedelta(minutes=15)
        
        if now_dt >= grace_period_end:
            print(f"Force closing stale session ID={session.id} for Employee {session.attendance.employee.username}")
            
            ot = Overtime.objects.filter(session=session, status='PENDING').first()
            if ot:
                ot.status = 'REJECTED'
                ot.admin_remarks = 'AUTO_REJECTED_STALE'
                ot.save()
            
            session.check_out_time = now_dt.time()
            session.auto_checkout = True
            session.ot_status = 'REJECTED'
            session.save()
            
            AttendanceService._recalculate_attendance_metrics(session.attendance, shift, att_date)
            
            AttendanceAuditLog.objects.create(
                session=session,
                user=None,
                old_value={"check_out_time": None, "auto_checkout": False},
                new_value={"check_out_time": str(session.check_out_time), "auto_checkout": True},
                reason="PRODUCTION_ONE_TIME_CLEANUP"
            )
            count += 1
            
    print(f"Cleanup complete. Closed {count} sessions.")

if __name__ == "__main__":
    cleanup()
