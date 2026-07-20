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

            old_status = attendance.status
            
            # Recalculate status using the updated services logic
            # We don't want to mess up total_worked_hours or check-in, so just sync metrics
            AttendanceService._recalculate_attendance_metrics(attendance, shift, attendance.date)
            
            new_status = attendance.status
            if old_status != new_status or attendance.shift_id != shift.id:
                self.stdout.write(
                    f"[{employee.username}] {attendance.date} | "
                    f"Old: {old_status} -> New: {new_status} | "
                    f"Shift: {shift.name} ({shift.start_time}) | CheckIn: {attendance.check_in_time}"
                )
                attendance.shift = shift
                attendance.save()
                fixed_count += 1
                
        self.stdout.write(self.style.SUCCESS(f"Recalculation complete. Fixed {fixed_count} records out of {total_count}."))
