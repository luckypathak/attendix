import os
import django
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
django.setup()

from attendix.apps.attendance.models import Attendance
print("Total Attendance records:", Attendance.objects.count())
print("Records for 2026-07-19:")
for a in Attendance.objects.filter(date='2026-07-19'):
    print(f"ID: {a.id}, Status: {a.status}, Emp: {a.employee.username}")
print("Records for 2026-07-18:")
for a in Attendance.objects.filter(date='2026-07-18'):
    print(f"ID: {a.id}, Status: {a.status}, Emp: {a.employee.username}")
