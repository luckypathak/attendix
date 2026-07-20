import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
# Do NOT load dotenv
django.setup()

from attendix.apps.attendance.models import Attendance
from django.contrib.auth import get_user_model

User = get_user_model()
print("Total Users:", User.objects.count())
print("Total Attendance records:", Attendance.objects.count())
print("Records for 2026-07-19:")
for a in Attendance.objects.filter(date='2026-07-19'):
    print(f"ID: {a.id}, Status: {a.status}, Emp: {a.employee.username}")
print("Records for 2026-07-18:")
for a in Attendance.objects.filter(date='2026-07-18'):
    print(f"ID: {a.id}, Status: {a.status}, Emp: {a.employee.username}")
