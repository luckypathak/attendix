import os
import sys
import django

sys.path.append('/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
django.setup()

from attendix.apps.attendance.models import AttendanceSession

active_sessions = AttendanceSession.objects.filter(check_out_time__isnull=True).select_related('attendance__employee')
for s in active_sessions:
    print(f"Session ID {s.id} | Employee: {s.attendance.employee.username} | Check-in: {s.check_in_time} | Date: {s.attendance.date}")
