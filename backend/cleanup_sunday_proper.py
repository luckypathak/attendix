import os
import django
from datetime import date
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
django.setup()

from attendix.apps.attendance.models import Attendance

today = date(2026, 7, 19)
deleted_count, _ = Attendance.objects.filter(date=today, status=Attendance.Statuses.ABSENT).delete()
print(f"Proper DB: Deleted {deleted_count} mistakenly marked ABSENT records for Sunday, {today}")

