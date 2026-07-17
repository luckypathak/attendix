import os
import sys
import django
from datetime import time, timedelta
from django.utils import timezone

sys.path.append('/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
django.setup()

from attendix.apps.attendance.models import Attendance, AttendanceSession, Shift
from attendix.apps.company.models import Company
from django.contrib.auth import get_user_model
from attendix.apps.attendance.services import AttendanceService

User = get_user_model()

print("Setting up test data...")
company, _ = Company.objects.get_or_create(name="AutoCheckout Test Company")
user, _ = User.objects.get_or_create(username="autocheckout_user", company=company, role="EMPLOYEE")
shift, _ = Shift.objects.get_or_create(company=company, name="Test Shift", start_time=time(11, 0), end_time=time(20, 0), grace_period_minutes=15)

AttendanceSession.objects.filter(attendance__employee=user).delete()
Attendance.objects.filter(employee=user).delete()

# Create active session today
att = Attendance.objects.create(employee=user, date=timezone.now().date(), status='PRESENT', shift=shift)
sess = AttendanceSession.objects.create(attendance=att, check_in_time=time(11, 0))

print(f"Created active session. ID={sess.id}")

# Run logic
now_dt = timezone.localtime(timezone.now())
print(f"Current local time: {now_dt}")
shift_end_dt = timezone.make_aware(timezone.datetime.combine(att.date, shift.end_time), timezone.get_current_timezone())
window_end = shift_end_dt + timedelta(minutes=15)
print(f"Shift end dt: {shift_end_dt}")
print(f"Window end dt: {window_end}")
print(f"now_dt > window_end: {now_dt > window_end}")

print("Running check_active_overtimes_and_autocheckout...")
AttendanceService.check_active_overtimes_and_autocheckout()

sess.refresh_from_db()
print(f"Session check_out_time: {sess.check_out_time}")
print(f"Session auto_checkout: {sess.auto_checkout}")
