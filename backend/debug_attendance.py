import os
import django
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
django.setup()

from attendix.apps.attendance.models import Attendance
from attendix.apps.attendance.services import AttendanceService
from django.utils import timezone

def run():
    records = Attendance.objects.all()
    
    for attendance in records:
        employee = attendance.employee
        shift = AttendanceService.get_active_shift(employee)
        print(f"[{employee.username}] {attendance.date} | DB Status: {attendance.status} | DB Shift: {attendance.shift} | Profile Shift: {shift} | CheckIn: {attendance.check_in_time}")

if __name__ == '__main__':
    run()
