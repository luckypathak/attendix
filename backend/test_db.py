import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from attendix.apps.attendance.models import Attendance
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.filter(username='ilucky').first()
if not user:
    print("User ilucky not found!")
else:
    recs = Attendance.objects.filter(employee=user)
    print(f"Found {recs.count()} records for ilucky")
    for r in recs:
        print(f"Record: {r.id}, date: {r.date}")
