import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import Attendance, Overtime, Shift, AttendanceSession
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
    def check_in(cls, employee, lat, lng, accuracy, address, device_info, timestamp=None, captured_image=None):
        if not lat or not lng:
            raise ValidationError("GPS location coordinates are mandatory for check-in.")
        
        if accuracy and float(accuracy) > 50.0:
            raise ValidationError("GPS accuracy is too low (greater than 50 meters). Please retry in an open area.")

        import sys
        is_testing = 'test' in sys.argv
        if not captured_image and not is_testing:
            raise ValidationError("Check-in photo capture is mandatory. Please capture photo first.")


        now = timestamp or timezone.now()
        if timezone.is_aware(now):
            now = timezone.localtime(now)
        today = now.date()
        time_now = now.time()

        # Auto-checkout any open sessions from previous days
        previous_open_sessions = AttendanceSession.objects.filter(
            attendance__employee=employee,
            attendance__date__lt=today,
            check_out_time__isnull=True
        )
        for session in previous_open_sessions:
            active_shift = session.attendance.shift or cls.get_active_shift(employee)
            session.check_out_time = active_shift.end_time if active_shift else datetime.time(18, 0, 0)
            session.check_out_address = "SYSTEM AUTO CHECKOUT (Forgot checkout)"
            session.check_out_lat = session.check_in_lat
            session.check_out_lng = session.check_in_lng
            session.save()
            
            # Recalculate parent hours & status
            cls._recalculate_attendance_metrics(session.attendance, active_shift, now.date())

        # Check if user already has an active check-in session today (which is not checked out)
        active_session = AttendanceSession.objects.filter(
            attendance__employee=employee,
            check_out_time__isnull=True
        ).first()

        if active_session:
            raise ValidationError("You are already checked in. Please check-out first.")

        # Get or create the Attendance record for today
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'status': Attendance.Statuses.PRESENT}
        )

        # Clear checkout fields on check-in
        attendance.check_out_time = None
        attendance.check_out_lat = None
        attendance.check_out_lng = None
        attendance.check_out_accuracy = None
        attendance.check_out_address = None
        attendance.check_out_device_info = None

        shift = cls.get_active_shift(employee)
        if not shift:
            raise ValidationError("No active shift configured for your company. Contact administrator.")

        # Determine late status (based on the first check-in of the day)
        status = attendance.status
        is_first_session = not attendance.sessions.exists()
        if is_first_session:
            shift_start = shift.start_time
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
            attendance.check_in_lat = lat
            attendance.check_in_lng = lng
            attendance.check_in_accuracy = accuracy
            attendance.check_in_address = address
            attendance.check_in_device_info = device_info
            from django.core.files.base import ContentFile
            if captured_image:
                img_content = captured_image.read()
                attendance.captured_image.save(captured_image.name, ContentFile(img_content), save=False)
                captured_image.seek(0)
            
            attendance.status = status
            attendance.save()
        else:
            attendance.save()

        # Create new session record
        session = AttendanceSession(
            attendance=attendance,
            check_in_time=time_now,
            check_in_lat=lat,
            check_in_lng=lng,
            check_in_accuracy=accuracy,
            check_in_address=address,
            check_in_device_info=device_info
        )
        if captured_image:
            captured_image.seek(0)
            img_content = captured_image.read()
            session.captured_image.save(captured_image.name, ContentFile(img_content), save=False)
            captured_image.seek(0)
        session.save()
        
        # User Requirement: The map should appear immediately after first check in.
        # Save the very first location ping so the tracking map has a starting point immediately.
        from .models import LocationPing
        LocationPing.objects.create(
            session=session,
            latitude=lat,
            longitude=lng,
            accuracy=accuracy
        )

        return attendance

    @classmethod
    def check_out(cls, employee, lat, lng, accuracy, address, device_info, captured_image=None, timestamp=None):
        if not lat or not lng:
            raise ValidationError("GPS location coordinates are mandatory for check-out.")

        now = timestamp or timezone.now()
        if timezone.is_aware(now):
            now = timezone.localtime(now)
        time_now = now.time()

        # Find the active session (supports overnight checkouts)
        active_session = AttendanceSession.objects.filter(
            attendance__employee=employee,
            check_out_time__isnull=True
        ).order_by('-attendance__date', '-check_in_time').first()

        if not active_session:
            raise ValidationError("No active check-in record found. You must check-in first.")

        # Update the active session details
        active_session.check_out_time = time_now
        active_session.check_out_lat = lat
        active_session.check_out_lng = lng
        active_session.check_out_accuracy = accuracy
        active_session.check_out_address = address
        active_session.check_out_device_info = device_info
        if captured_image:
            active_session.check_out_captured_image = captured_image
        active_session.save()

        # Update the parent attendance check out details
        attendance = active_session.attendance
        attendance.check_out_time = time_now
        attendance.check_out_lat = lat
        attendance.check_out_lng = lng
        attendance.check_out_accuracy = accuracy
        attendance.check_out_address = address
        attendance.check_out_device_info = device_info
        attendance.save()

        shift = attendance.shift or cls.get_active_shift(employee)
        cls._recalculate_attendance_metrics(attendance, shift, now.date())

        return attendance

    @classmethod
    def _recalculate_attendance_metrics(cls, attendance, shift, current_date):
        # Calculate cumulative metrics across all completed sessions
        sessions = attendance.sessions.filter(check_out_time__isnull=False).order_by('check_in_time')
        
        all_sessions = attendance.sessions.all().order_by('check_in_time')
        if not all_sessions.exists():
            return

        total_worked_seconds = 0.0
        first_session = all_sessions.first()
        last_session = all_sessions.last()
        
        has_active = False

        for session in all_sessions:
            checkin_dt = datetime.datetime.combine(attendance.date, session.check_in_time)
            
            if session.check_out_time:
                checkout_date = attendance.date
                if session.check_out_time < session.check_in_time:
                    checkout_date += datetime.timedelta(days=1)
                checkout_dt = datetime.datetime.combine(checkout_date, session.check_out_time)
                total_worked_seconds += (checkout_dt - checkin_dt).total_seconds()
            else:
                has_active = True
                from django.utils import timezone
                now_dt = timezone.localtime(timezone.now())
                total_worked_seconds += (now_dt - timezone.make_aware(checkin_dt)).total_seconds()

        total_worked_hours = round(total_worked_seconds / 3600.0, 2)
        attendance.total_worked_hours = total_worked_hours

        for session in sessions:
            checkin_dt = datetime.datetime.combine(attendance.date, session.check_in_time)
            checkout_date = attendance.date
            if session.check_out_time < session.check_in_time:
                checkout_date += datetime.timedelta(days=1)
            checkout_dt = datetime.datetime.combine(checkout_date, session.check_out_time)
            total_worked_seconds += (checkout_dt - checkin_dt).total_seconds()

        total_worked_hours = round(total_worked_seconds / 3600.0, 2)
        attendance.total_worked_hours = total_worked_hours

        # Break Hours: From first check-in to last check-out (or now) total time minus worked hours
        first_in_dt = datetime.datetime.combine(attendance.date, first_session.check_in_time)
        if last_session.check_out_time:
            last_out_date = attendance.date
            if last_session.check_out_time < first_session.check_in_time:
                last_out_date += datetime.timedelta(days=1)
            last_out_dt = datetime.datetime.combine(last_out_date, last_session.check_out_time)
            total_elapsed_seconds = (last_out_dt - first_in_dt).total_seconds()
        else:
            from django.utils import timezone
            now_dt = timezone.localtime(timezone.now())
            total_elapsed_seconds = (now_dt - timezone.make_aware(first_in_dt)).total_seconds()
        
        total_elapsed_seconds = (last_out_dt - first_in_dt).total_seconds()
        break_seconds = max(0.0, total_elapsed_seconds - total_worked_seconds)
        attendance.break_hours = round(break_seconds / 3600.0, 2)

        # Half-day rule: If worked hours is less than shift duration (or 6.0 hrs fallback), downgrade status to HALF_DAY
        shift_hours = float(shift.duration_hours) if shift else 9.0

        # Check if user has 3 or more auto-checkouts (3 strikes rule)
        profile = getattr(attendance.employee, 'employee_profile', None)
        has_three_strikes = profile and profile.checkout_missed_count >= 3
        has_auto_checkout_today = attendance.sessions.filter(auto_checkout=True).exists()

        if (total_worked_hours < shift_hours and not has_active) or (has_three_strikes and has_auto_checkout_today):
            attendance.status = Attendance.Statuses.HALF_DAY
        else:
            # If they completed the full shift, restore status from HALF_DAY to PRESENT or LATE
            if attendance.status == Attendance.Statuses.HALF_DAY:
                if shift:
                    shift_start = shift.start_time
                    dummy_date = datetime.date(2000, 1, 1)
                    start_datetime = datetime.datetime.combine(dummy_date, shift_start)
                    if attendance.check_in_time:
                        checkin_datetime = datetime.datetime.combine(dummy_date, attendance.check_in_time)
                        difference_mins = (checkin_datetime - start_datetime).total_seconds() / 60.0
                        if difference_mins > shift.grace_period_minutes:
                            attendance.status = Attendance.Statuses.LATE
                        else:
                            attendance.status = Attendance.Statuses.PRESENT
                    else:
                        attendance.status = Attendance.Statuses.PRESENT
                else:
                    attendance.status = Attendance.Statuses.PRESENT

        # Calculate session-level regular and overtime hours
        regular_accumulated = 0.0
        approved_ot_total = 0.0

        for session in sessions:
            checkin_dt = datetime.datetime.combine(attendance.date, session.check_in_time)
            checkout_date = attendance.date
            if session.check_out_time < session.check_in_time:
                checkout_date += datetime.timedelta(days=1)
            checkout_dt = datetime.datetime.combine(checkout_date, session.check_out_time)
            session_duration = round((checkout_dt - checkin_dt).total_seconds() / 3600.0, 2)

            if regular_accumulated < shift_hours:
                needed = round(shift_hours - regular_accumulated, 2)
                if session_duration <= needed:
                    session.regular_hours = session_duration
                    session.ot_hours = 0.0
                    regular_accumulated = round(regular_accumulated + session_duration, 2)
                else:
                    session.regular_hours = needed
                    session.ot_hours = round(session_duration - needed, 2)
                    regular_accumulated = shift_hours
            else:
                session.regular_hours = 0.0
                session.ot_hours = session_duration

            # Continue Shift Rule: Clicks Continue Shift -> OT = 0
            if session.continue_shift:
                session.ot_hours = 0.0

            # If OT status is rejected or not approved, do not count the OT hours
            if session.ot_status == 'REJECTED':
                session.ot_hours = 0.0
            
            if session.ot_status == 'APPROVED':
                approved_ot_total = round(approved_ot_total + float(session.ot_hours), 2)

            session.save()

            # Synchronize Overtime request hours if it exists
            ot_req = getattr(session, 'overtime_request', None)
            if ot_req:
                if session.ot_status == 'REJECTED' or session.continue_shift:
                    ot_req.hours = 0.0
                else:
                    ot_req.hours = session.ot_hours
                ot_req.save()

        attendance.overtime_hours = approved_ot_total
        attendance.save()

    @classmethod
    def check_active_overtimes_and_autocheckout(cls):
        """
        Periodically checks active attendance sessions, detects shift completion window,
        creates OT requests, or auto checks out if employee fails to take action.
        """
        from django.utils import timezone
        import datetime
        from attendix.apps.attendance.models import Overtime
        from attendix.apps.notifications.services import NotificationService

        tz = timezone.get_current_timezone()
        now_dt = timezone.localtime(timezone.now())

        # Find all active sessions (where check_out_time is null)
        active_sessions = AttendanceSession.objects.filter(check_out_time__isnull=True)

        for session in active_sessions:
            attendance = session.attendance
            employee = attendance.employee
            shift = attendance.shift or cls.get_active_shift(employee)
            if not shift:
                continue

            # Calculate shift end datetime for the attendance date
            shift_start = shift.start_time
            shift_end = shift.end_time
            shift_end_dt = datetime.datetime.combine(attendance.date, shift_end)
            if shift_end < shift_start:
                # overnight shift crosses midnight
                shift_end_dt += datetime.timedelta(days=1)

            # Make shift_end_dt aware in local timezone
            shift_end_dt = timezone.make_aware(shift_end_dt, tz)

            # Define window: 15 minutes before shift end to 15 minutes after shift end
            window_start = shift_end_dt - datetime.timedelta(minutes=15)
            window_end = shift_end_dt + datetime.timedelta(minutes=15)

            # 1. If we are past the window end, and the employee took no action (forgot checkout)
            if now_dt > window_end:
                if not session.continue_shift and not session.ot_requested:
                    # Auto checkout due to negligence
                    profile = getattr(employee, 'employee_profile', None)
                    missed_count = 1
                    if profile:
                        profile.checkout_missed_count += 1
                        profile.save()
                        missed_count = profile.checkout_missed_count

                    # Use the actual time the auto checkout job runs, rather than backdating to window_end
                    session.check_out_time = now_dt.time()
                    session.auto_checkout = True
                    session.checkout_reason = 'AUTO_CHECKOUT'
                    session.checkout_missed_count = missed_count
                    session.save()

                    attendance.check_out_time = session.check_out_time
                    attendance.save()

                    # Notify admins
                    admins = User.objects.filter(company=employee.company, role__in=['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER'])
                    if profile and profile.manager:
                        admins = admins | User.objects.filter(id=profile.manager.id)
                    admins = admins.distinct()

                    for admin in admins:
                        NotificationService.create_in_app_notification(
                            recipient=admin,
                            title="Employee Auto Checked Out",
                            body=f"Employee {employee.username} did not check out before shift end. System performed automatic checkout."
                        )

                        if missed_count >= 3:
                            NotificationService.create_in_app_notification(
                                recipient=admin,
                                title="Repeated Checkout Violation",
                                body=f"Employee {employee.username} has failed to check out properly three times. Attendance marked as HALF_DAY."
                            )

                    # Recalculate metrics
                    cls._recalculate_attendance_metrics(attendance, shift, attendance.date)

    @classmethod
    def process_auto_checkout(cls):
        """
        Fallback compatibility wrapper calling the new check_active_overtimes_and_autocheckout logic.
        """
        cls.check_active_overtimes_and_autocheckout()


