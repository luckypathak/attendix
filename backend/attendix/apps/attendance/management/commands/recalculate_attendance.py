import datetime
from django.core.management.base import BaseCommand
from attendix.apps.attendance.models import Attendance
from attendix.apps.attendance.services import AttendanceService
from django.utils import timezone

class Command(BaseCommand):
    help = 'Recalculates attendance statuses using the correct employee shift logic.'

    def handle(self, *args, **options):
        records = Attendance.objects.filter(check_in_time__isnull=False)
        fixed_count = 0
        total_count = records.count()
        
        self.stdout.write(self.style.WARNING(f"Recalculating status for {total_count} attendance records..."))
        
        for attendance in records:
            employee = attendance.employee
            shift = AttendanceService.get_active_shift(employee)
            
            if not shift:
                continue
                
            shift_start = shift.start_time
            time_now = attendance.check_in_time
            today = attendance.date
            
            dummy_date = datetime.date(2000, 1, 1)
            start_datetime = datetime.datetime.combine(dummy_date, shift_start)
            checkin_datetime = datetime.datetime.combine(dummy_date, time_now)
            
            difference_mins = (checkin_datetime - start_datetime).total_seconds() / 60.0
            
            status = Attendance.Statuses.PRESENT
            if difference_mins > shift.grace_period_minutes:
                start_of_month = today.replace(day=1)
                late_count = Attendance.objects.filter(
                    employee=employee,
                    date__gte=start_of_month,
                    date__lt=today,
                    status__in=[Attendance.Statuses.LATE, Attendance.Statuses.HALF_DAY]
                ).count()

                company_settings = employee.company
                late_limit = company_settings.late_limit_for_half_day if company_settings else 3

                if late_count >= late_limit:
                    status = Attendance.Statuses.HALF_DAY
                else:
                    status = Attendance.Statuses.LATE
                    
            if attendance.status != status or attendance.shift_id != shift.id:
                self.stdout.write(
                    f"[{employee.username}] {today} | "
                    f"Old: {attendance.status} -> New: {status} | "
                    f"Shift: {shift.name} ({shift.start_time}) | CheckIn: {time_now}"
                )
                attendance.status = status
                attendance.shift = shift
                attendance.save()
                fixed_count += 1
                
        self.stdout.write(self.style.SUCCESS(f"Recalculation complete. Fixed {fixed_count} records out of {total_count}."))
