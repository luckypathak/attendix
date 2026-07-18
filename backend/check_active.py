import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from attendix.apps.attendance.models import AttendanceSession

sessions = AttendanceSession.objects.filter(check_out_time__isnull=True)
for s in sessions:
    print(s.attendance.employee.username, s.id, s.check_in_time, s.auto_checkout)
