import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from attendix.apps.attendance.models import AttendanceSession, AttendanceAuditLog

sessions = AttendanceSession.objects.filter(auto_checkout=True)
for s in sessions:
    logs = AttendanceAuditLog.objects.filter(session=s)
    print(s.attendance.employee.username, s.id, s.check_out_time, s.checkout_reason, len(logs))
