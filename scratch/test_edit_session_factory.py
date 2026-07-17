import os
import sys
import django
from datetime import time, timedelta
from django.utils import timezone
from django.test.client import RequestFactory

sys.path.append('/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
django.setup()

from attendix.apps.attendance.models import Attendance, AttendanceSession, Shift, AttendanceAuditLog
from attendix.apps.attendance.views import AttendanceViewSet
from attendix.apps.company.models import Company
from django.contrib.auth import get_user_model

User = get_user_model()

print("Setting up edit session test data...")
company = Company.objects.first()
admin_user = User.objects.filter(role='SUPER_ADMIN').first()
emp_user = User.objects.filter(role='EMPLOYEE', company=company).first()
shift = Shift.objects.filter(company=company).first()

# Create a sample past attendance
Attendance.objects.filter(employee=emp_user, date=timezone.now().date() - timedelta(days=3)).delete()
att = Attendance.objects.create(employee=emp_user, date=timezone.now().date() - timedelta(days=3), status='LATE', shift=shift)
sess = AttendanceSession.objects.create(attendance=att, check_in_time=time(12, 0), check_out_time=time(18, 0))

# Recalculate original hours
from attendix.apps.attendance.services import AttendanceService
AttendanceService._recalculate_attendance_metrics(att, shift, att.date)
att.refresh_from_db()
sess.refresh_from_db()

print(f"Original status: {att.status}, Original Work Hours: {att.total_worked_hours}, original OT: {att.overtime_hours}")

factory = RequestFactory()
request = factory.patch('/api/attendance/records/edit-session/', {
    'session_id': sess.id,
    'reason': 'Adjusting check-in time because employee forgot to check in initially',
    'check_in_time': '10:00:00',
    'status': 'PRESENT'
}, content_type='application/json')
request.user = admin_user

view = AttendanceViewSet.as_view({'patch': 'edit_session'})
response = view(request)

print(f"Response status: {response.status_code}")
if response.status_code == 200:
    att.refresh_from_db()
    sess.refresh_from_db()
    print(f"New status: {att.status}, New Work Hours: {att.total_worked_hours}, New check in: {sess.check_in_time}")
    
    # Check audit log
    logs = AttendanceAuditLog.objects.filter(session=sess)
    print(f"Audit logs count: {logs.count()}")
    for log in logs:
        print(f"Log: Reason={log.reason}, Old={log.old_value['check_in_time']}, New={log.new_value['check_in_time']}")
else:
    print(f"Error: {response.data}")

