import os
import django
from datetime import date
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
django.setup()

from attendix.apps.attendance.models import Attendance

print("All recent Attendance records:")
for a in Attendance.objects.order_by('-date')[:15]:
    print(f"ID: {a.id}, Date: {a.date}, Employee: {a.employee.username}, Status: {a.status}, Deleted: {a.is_deleted}")

