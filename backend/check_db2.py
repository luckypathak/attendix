import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_yNGsD6wpd7Fg@ep-flat-tree-at-a51ed9r3-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require'
django.setup()

from attendix.apps.attendance.models import Attendance

print("Recent attendance records:")
for a in Attendance.objects.all().order_by('-date')[:10]:
    print(f"{a.date} | {a.employee.username} | {a.status}")

