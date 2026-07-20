import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_yNGsD6wpd7Fg@ep-flat-tree-at7ps4y8.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require'
os.environ['IS_PRODUCTION'] = 'true'

django.setup()

from attendix.apps.attendance.models import Attendance

target_date = date(2026, 7, 18)
missing_checkouts = Attendance.objects.filter(date=target_date, check_in_time__isnull=False, check_out_time__isnull=True)

if not missing_checkouts.exists():
    print("Koi bhi nahi! Sabhi ne check out kar liya tha ya kisi ne check in hi nahi kiya tha 18 July ko.")
else:
    print(f"Total {missing_checkouts.count()} log aise hain jinka checkout nahi hua 18 July ko:")
    for att in missing_checkouts:
        print(f"- {att.employee.get_full_name()} (Username: {att.employee.username}) | Check In Time: {att.check_in_time}")
