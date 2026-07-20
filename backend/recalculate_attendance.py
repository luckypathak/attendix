import os
import django
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
django.setup()

from attendix.apps.attendance.models import Attendance
from attendix.apps.attendance.services import AttendanceService
from django.utils import timezone

def run():
    records = Attendance.objects.filter(check_in_time__isnull=False)
    fixed_count = 0
    total_count = records.count()
    
    print(f"Recalculating status for {total_count} attendance records...")
    
    for attendance in records:
        employee = attendance.employee
        shift = AttendanceService.get_active_shift(employee)
        
        if not shift:
            # If no shift assigned, skip recalculation as we can't determine late.
            continue
            
        # We need to re-evaluate late based on shift
        shift_start = shift.start_time
        time_now = attendance.check_in_time
        today = attendance.date
        
        dummy_date = datetime.date(2000, 1, 1)
        start_datetime = datetime.datetime.combine(dummy_date, shift_start)
        checkin_datetime = datetime.datetime.combine(dummy_date, time_now)
        
        difference_mins = (checkin_datetime - start_datetime).total_seconds() / 60.0
        
        status = Attendance.Statuses.PRESENT
        if difference_mins > shift.grace_period_minutes:
            # Check how many late arrivals in the current month prior to this day
            start_of_month = today.replace(day=1)
            # Find previous records in the month to count lates correctly.
            late_count = Attendance.objects.filter(
                employee=employee,
                date__gte=start_of_month,
                date__lt=today, # strictly before today
                status__in=[Attendance.Statuses.LATE, Attendance.Statuses.HALF_DAY]
            ).count()

            company_settings = employee.company
            late_limit = company_settings.late_limit_for_half_day if company_settings else 3

            if late_count >= late_limit:
                status = Attendance.Statuses.HALF_DAY
            else:
                status = Attendance.Statuses.LATE
                
        # Also, check if it was marked absent manually? If it was check_in_time exists it shouldn't be absent, but just in case.
        
        if attendance.status != status or attendance.shift_id != shift.id:
            print(f"[{employee.username}] {today} | Old Status: {attendance.status} | New Status: {status} | Shift: {shift.name} ({shift.start_time}) | CheckIn: {time_now}")
            attendance.status = status
            attendance.shift = shift
            attendance.save()
            fixed_count += 1
            
    print(f"\nRecalculation complete. Fixed {fixed_count} records out of {total_count}.")

if __name__ == '__main__':
    run()
