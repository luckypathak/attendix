import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import Attendance, Overtime, Shift
from django.contrib.auth import get_user_model

User = get_user_model()


class AttendanceService:
    @staticmethod
    def get_active_shift(employee):
        # Retrieve employee's shift. If not configured, fall back to first shift of company or default
        profile = getattr(employee, 'employee_profile', None)
        if profile and profile.department:
            # We can find a shift assigned to user or department. Let's fetch default shift.
            shift = Shift.objects.filter(company=employee.company).first()
            return shift
        return Shift.objects.filter(company=employee.company).first()

    @classmethod
    def check_in(cls, employee, lat, lng, accuracy, address, device_info, timestamp=None):
        if not lat or not lng:
            raise ValidationError("GPS location coordinates are mandatory for check-in.")
        
        if accuracy and float(accuracy) > 50.0:
            raise ValidationError("GPS accuracy is too low (greater than 50 meters). Please retry in an open area.")

        now = timestamp or timezone.now()
        if timezone.is_aware(now):
            now = timezone.localtime(now)
        today = now.date()
        time_now = now.time()

        # Auto-checkout any open records from previous days
        previous_open_records = Attendance.objects.filter(
            employee=employee,
            date__lt=today,
            check_in_time__isnull=False,
            check_out_time__isnull=True
        )
        for record in previous_open_records:
            active_shift = record.shift or cls.get_active_shift(employee)
            record.check_out_time = active_shift.end_time if active_shift else datetime.time(18, 0, 0)
            record.check_out_address = "SYSTEM AUTO CHECKOUT (Forgot checkout)"
            record.check_out_lat = record.check_in_lat
            record.check_out_lng = record.check_in_lng
            
            # Half-day rule check for auto-closed records
            chk_in_dt = datetime.datetime.combine(record.date, record.check_in_time)
            chk_out_dt = datetime.datetime.combine(record.date, record.check_out_time)
            hrs = (chk_out_dt - chk_in_dt).total_seconds() / 3600.0
            if hrs < 6.0:
                record.status = Attendance.Statuses.HALF_DAY
            record.save()

        # Check if already checked in today
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'status': Attendance.Statuses.PRESENT}
        )

        if not created and attendance.check_in_time is not None:
            raise ValidationError("You have already checked in today.")

        shift = cls.get_active_shift(employee)
        if not shift:
            raise ValidationError("No active shift configured for your company. Contact administrator.")

        # Determine late status
        shift_start = shift.start_time
        # Convert to datetime for math
        dummy_date = datetime.date(2000, 1, 1)
        start_datetime = datetime.datetime.combine(dummy_date, shift_start)
        checkin_datetime = datetime.datetime.combine(dummy_date, time_now)
        
        difference_mins = (checkin_datetime - start_datetime).total_seconds() / 60.0

        status = Attendance.Statuses.PRESENT
        if difference_mins > shift.grace_period_minutes:
            # Check how many late arrivals in the current month
            start_of_month = today.replace(day=1)
            late_count = Attendance.objects.filter(
                employee=employee,
                date__gte=start_of_month,
                date__lte=today,
                status__in=[Attendance.Statuses.LATE, Attendance.Statuses.HALF_DAY]
            ).count()

            company_settings = employee.company
            late_limit = company_settings.late_limit_for_half_day if company_settings else 3

            if late_count >= late_limit:
                status = Attendance.Statuses.HALF_DAY
            else:
                status = Attendance.Statuses.LATE

        attendance.shift = shift
        attendance.check_in_time = time_now
        attendance.status = status
        attendance.check_in_lat = lat
        attendance.check_in_lng = lng
        attendance.check_in_accuracy = accuracy
        attendance.check_in_address = address
        attendance.check_in_device_info = device_info
        attendance.save()

        return attendance

    @classmethod
    def check_out(cls, employee, lat, lng, accuracy, address, device_info, timestamp=None):
        if not lat or not lng:
            raise ValidationError("GPS location coordinates are mandatory for check-out.")

        now = timestamp or timezone.now()
        if timezone.is_aware(now):
            now = timezone.localtime(now)
        time_now = now.time()

        # Find the most recent active check-in (supports overnight shift checkout on the next day)
        attendance = Attendance.objects.filter(
            employee=employee,
            check_in_time__isnull=False,
            check_out_time__isnull=True
        ).order_by('-date', '-check_in_time').first()

        if not attendance:
            raise ValidationError("No active check-in record found. You must check-in first.")

        attendance.check_out_time = time_now
        attendance.check_out_lat = lat
        attendance.check_out_lng = lng
        attendance.check_out_accuracy = accuracy
        attendance.check_out_address = address
        attendance.check_out_device_info = device_info

        # Calculate duration of work
        checkin_dt = datetime.datetime.combine(attendance.date, attendance.check_in_time)
        checkout_dt = datetime.datetime.combine(now.date(), time_now)
        hours_worked = (checkout_dt - checkin_dt).total_seconds() / 3600.0

        # Half-day rule: If worked hours is less than 6 hours, downgrade status to HALF_DAY
        if hours_worked < 6.0:
            attendance.status = Attendance.Statuses.HALF_DAY

        attendance.save()

        # Overtime calculation
        shift = attendance.shift or cls.get_active_shift(employee)
        if shift:
            shift_end_datetime = datetime.datetime.combine(attendance.date, shift.end_time)
            
            # If they checked out after shift end time
            if checkout_dt > shift_end_datetime:
                overtime_seconds = (checkout_dt - shift_end_datetime).total_seconds()
                overtime_hours = round(overtime_seconds / 3600.0, 2)
                
                if overtime_hours >= 0.5: # At least 30 minutes overtime to trigger a request
                    Overtime.objects.get_or_create(
                        employee=employee,
                        attendance=attendance,
                        date=attendance.date,
                        defaults={
                            'hours': overtime_hours,
                            'status': 'PENDING'
                        }
                    )

        return attendance

    @classmethod
    def process_auto_checkout(cls):
        """
        Runs via Celery beat. Auto check-out employees who forgot to check out
        after shift completion + grace period (default 10 hours of shift).
        """
        today = timezone.now().date()
        # Find active check-ins that do not have a check-out time
        pending_checkouts = Attendance.objects.filter(
            date=today,
            check_in_time__isnull=False,
            check_out_time__isnull=True
        )

        for record in pending_checkouts:
            company = record.employee.company
            auto_checkout_hrs = float(company.auto_checkout_hours) if company else 10.0
            
            checkin_dt = datetime.datetime.combine(record.date, record.check_in_time)
            now_dt = datetime.datetime.now()
            
            hours_elapsed = (now_dt - checkin_dt).total_seconds() / 3600.0
            
            if hours_elapsed >= auto_checkout_hrs:
                # Check if there is an approved OT before auto-checking out
                ot_request = Overtime.objects.filter(attendance=record).first()
                if ot_request and ot_request.status == 'APPROVED':
                    continue # Employee has approved overtime, do not auto checkout
                
                # Perform auto checkout
                record.check_out_time = record.shift.end_time if record.shift else datetime.time(18, 0, 0)
                record.check_out_address = "SYSTEM AUTO CHECKOUT (Forgotten checkout)"
                record.check_out_lat = record.check_in_lat
                record.check_out_lng = record.check_in_lng
                record.save()
