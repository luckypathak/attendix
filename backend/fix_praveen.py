import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_yNGsD6wpd7Fg@ep-flat-tree-at-a51kofcw-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require'
django.setup()

from attendix.apps.attendance.models import Attendance
from attendix.apps.attendance.services import AttendanceService

atts = Attendance.objects.filter(date='2026-07-18')
for att in atts:
    AttendanceService._recalculate_attendance_metrics(att, att.shift, att.date)
    print(f"{att.employee.username}: status={att.status}, total_hours={att.total_worked_hours}")
