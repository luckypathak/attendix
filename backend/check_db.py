import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_yNGsD6wpd7Fg@ep-flat-tree-at-a51ed9r3-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require'
django.setup()

from attendix.apps.attendance.models import Attendance

today = date(2026, 7, 19)
print('Total:', Attendance.objects.filter(date=today).count())
print('Absent:', Attendance.objects.filter(date=today, status=Attendance.Statuses.ABSENT).count())
deleted, _ = Attendance.objects.filter(date=today, status=Attendance.Statuses.ABSENT).delete()
print('Deleted:', deleted)
