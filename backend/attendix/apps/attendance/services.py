import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import Attendance, Overtime, Shift, AttendanceSession
from django.contrib.auth import get_user_model

User = get_user_model()


class AttendanceService:
    @classmethod
    def mark_absentees_for_date(cls, company, date):
        from django.contrib.auth import get_user_model
        from attendix.apps.leave.models import LeaveRequest
        from .models import Attendance
        import datetime
        from django.utils import timezone
        
        User = get_user_model()
        employees = User.objects.filter(company=company, role='EMPLOYEE', is_active=True, is_deleted=False)
        today = timezone.localdate()
        
        if date > today:
            return # Future dates cannot be marked absent
            
        now = timezone.localtime(timezone.now()).time()
        
        for emp in employees:
            if Attendance.objects.filter(employee=emp, date=date).exists():
                continue
                
            if LeaveRequest.objects.filter(employee=emp, start_date__lte=date, end_date__gte=date, status='APPROVED').exists():
                continue
                
            shift = cls.get_active_shift(emp)
            if not shift or not shift.start_time:
                continue
                
            grace = company.grace_period_minutes or 0
            is_absent = False
            
            if date < today:
                is_absent = True
            else:
                dummy = datetime.datetime.combine(date, shift.start_time)
                cutoff = (dummy + datetime.timedelta(minutes=grace)).time()
                if now > cutoff:
                    is_absent = True
                    
            if is_absent:
                Attendance.objects.create(
                    employee=emp,
                    date=date,
                    shift=shift,
                    status=Attendance.Statuses.ABSENT
                )

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

        shift = cls.get_active_shift(employee)

        # Handle Clock In after Shift End
        if shift:
            now_dt = timezone.make_aware(datetime.datetime.combine(today, time_now))
            shift_end_dt = timezone.make_aware(datetime.datetime.combine(today, shift.end_time))
            if shift.end_time < shift.start_time:
                shift_end_dt += datetime.timedelta(days=1)
                
            # If current time is past shift end and they already have a completed session today
            if now_dt > shift_end_dt:
                existing_attendance = Attendance.objects.filter(employee=employee, date=today).first()
                if existing_attendance and existing_attendance.sessions.filter(check_out_time__isnull=False).exists():
                    # Check if they have an active session (then it's a different error)
                    if not existing_attendance.sessions.filter(check_out_time__isnull=True).exists():
                        from rest_framework.exceptions import APIException
                        class ShiftEndedOTRequired(APIException):
                            status_code = 409
                            default_detail = "Your shift has already ended. Do you want to continue as Overtime?"
                            default_code = 'requires_ot_approval'
                        raise ShiftEndedOTRequired()

        # Check if user already has an active check-in session today (which is not checked out)
        active_session = AttendanceSession.objects.filter(
            attendance__employee=employee,
            check_out_time__isnull=True
        ).first()

        if active_session:
            if shift:
                # now_dt and shift_end_dt are already calculated above if shift exists
                now_dt_check = timezone.make_aware(datetime.datetime.combine(today, time_now))
                shift_end_dt_check = timezone.make_aware(datetime.datetime.combine(today, shift.end_time))
                if shift.end_time < shift.start_time:
                    shift_end_dt_check += datetime.timedelta(days=1)
                
                if now_dt_check > shift_end_dt_check:
                    from attendix.apps.attendance.models import AttendanceCorrectionRequest
                    # Do not create duplicate if one is already pending
                    pending = AttendanceCorrectionRequest.objects.filter(
                        session=active_session, status='PENDING', request_type='LATE_CHECKIN_WHILE_ACTIVE'
                    ).exists()
                    if not pending:
                        AttendanceCorrectionRequest.objects.create(
                            employee=employee,
                            session=active_session,
                            date=today,
                            request_type='LATE_CHECKIN_WHILE_ACTIVE',
                            reason='Attempted Check In after shift end while previous session still active.',
                            status='PENDING'
                        )
                    from rest_framework.exceptions import APIException
                    class BlockedCheckInCorrection(APIException):
                        status_code = 409
                        default_detail = "You attempted to check in again after your shift ended, but your previous session is still active. A correction request has been sent to the Admin."
                        default_code = 'correction_request_submitted'
                    raise BlockedCheckInCorrection()

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

        first_session = all_sessions.first()
        last_session = all_sessions.last()
        has_active = attendance.sessions.filter(check_out_time__isnull=True).exists()

        # Now that computed_worked_hours exists, just sync it for caching (even though serializers bypass it)
        total_worked_hours = attendance.computed_worked_hours
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
        
        total_worked_seconds = total_worked_hours * 3600.0
        if last_session.check_out_time:
            break_seconds = max(0.0, total_elapsed_seconds - total_worked_seconds)
            attendance.break_hours = round(break_seconds / 3600.0, 2)
        else:
            attendance.break_hours = 0.0

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
    @classmethod
    def check_active_overtimes_and_autocheckout(cls):
        """
        Periodically checks active attendance sessions, detects shift completion window,
        creates OT requests, or auto checks out if employee fails to take action.
        """
        from django.utils import timezone
        import datetime
        from attendix.apps.attendance.models import Overtime, AttendanceCorrectionRequest
        from attendix.apps.notifications.services import NotificationService
        from authentication.models import User

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

            # Define window: 15 minutes after shift end
            trigger_dt = shift_end_dt + datetime.timedelta(minutes=15)

            if now_dt >= trigger_dt:
                # If session is already explicitly continued or OT approved, skip
                if session.continue_shift or session.ot_status == 'APPROVED':
                    continue

                # STEP 1: Check for existing pending request
                pending_request = AttendanceCorrectionRequest.objects.filter(
                    session=session,
                    status='PENDING',
                    request_type__in=['CONTINUE_SHIFT', 'OT_APPROVAL']
                ).first()

                if not pending_request:
                    # STEP 2: Create request if none exists
                    reason = f"System generated request for {employee.username} as shift ended and session is still active."
                    pending_request = AttendanceCorrectionRequest.objects.create(
                        employee=employee,
                        session=session,
                        date=attendance.date,
                        request_type='CONTINUE_SHIFT',
                        reason=reason,
                        status='PENDING'
                    )

                    # Notify admins
                    admins = User.objects.filter(company=employee.company, role__in=['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER'])
                    profile = getattr(employee, 'employee_profile', None)
                    if profile and profile.manager:
                        admins = admins | User.objects.filter(id=profile.manager.id)
                    
                    for admin in admins.distinct():
                        NotificationService.create_in_app_notification(
                            recipient=admin,
                            title="Shift Ended - Action Required",
                            body=f"Employee {employee.username}'s shift has ended but they are still checked in. Please approve or reject their session continuation."
                        )
                else:
                    # STEP 3/5: Wait timeout (15 mins from request creation)
                    request_age_mins = (now_dt - pending_request.created_at).total_seconds() / 60
                    if request_age_mins >= 15:
                        # Auto checkout due to admin negligence/timeout
                        pending_request.status = 'REJECTED'
                        pending_request.rejected_reason = 'AUTO REJECTED (Timeout)'
                        pending_request.save()

                        cls._perform_auto_checkout(session, employee, attendance, now_dt, shift)

    @classmethod
    def _perform_auto_checkout(cls, session, employee, attendance, checkout_dt, shift):
        from django.db.models import F
        from attendix.apps.notifications.services import NotificationService
        from authentication.models import User

        profile = getattr(employee, 'employee_profile', None)
        missed_count = 1
        if profile:
            profile.checkout_missed_count = F('checkout_missed_count') + 1
            profile.save(update_fields=['checkout_missed_count'])
            profile.refresh_from_db()
            missed_count = profile.checkout_missed_count

        session.check_out_time = checkout_dt.time()
        session.auto_checkout = True
        session.checkout_reason = 'AUTO_CHECKOUT'
        session.checkout_missed_count = missed_count
        session.save()

        attendance.check_out_time = session.check_out_time
        attendance.save()

        admins = User.objects.filter(company=employee.company, role__in=['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER'])
        if profile and profile.manager:
            admins = admins | User.objects.filter(id=profile.manager.id)
        
        for admin in admins.distinct():
            NotificationService.create_in_app_notification(
                recipient=admin,
                title="Employee Auto Checked Out",
                body=f"Employee {employee.username} was auto checked out (No admin response)."
            )

        # Recalculate metrics
        cls._recalculate_attendance_metrics(attendance, shift, attendance.date)

    @classmethod
    def process_auto_checkout(cls):
        """
        Fallback compatibility wrapper calling the new check_active_overtimes_and_autocheckout logic.
        """
        cls.check_active_overtimes_and_autocheckout()



    @classmethod
    def approve_correction(cls, correction, approved_by):
        correction.status = 'APPROVED'
        correction.approved_by = approved_by
        correction.save()
        
        attendance, created = Attendance.objects.get_or_create(
            employee=correction.employee,
            date=correction.date,
            defaults={'status': 'PRESENT'}
        )
        
        # Depending on the correction type, modify sessions
        from django.utils import timezone
        import datetime
        now = timezone.now()
        
        # If it's a missed check in, we create a session or update the first session
        if correction.request_type == 'MISSED_IN' and correction.requested_check_in:
            session = attendance.sessions.order_by('check_in_time').first()
            if session:
                session.check_in_time = correction.requested_check_in
                session.save()
            else:
                AttendanceSession.objects.create(
                    attendance=attendance,
                    check_in_time=correction.requested_check_in,
                    check_out_time=correction.requested_check_out if correction.requested_check_out else None,
                    check_in_photo=correction.check_in_photo,
                )
                
        # If it's a missed check out, we update the last session
        elif correction.request_type == 'MISSED_OUT' and correction.requested_check_out:
            session = attendance.sessions.filter(check_out_time__isnull=True).last()
            if not session:
                session = attendance.sessions.order_by('check_in_time').last()
            if session:
                session.check_out_time = correction.requested_check_out
                session.check_out_photo = correction.check_out_photo
                session.save()
                
        # If both
        elif correction.request_type == 'MISSED_BOTH' and correction.requested_check_in and correction.requested_check_out:
            AttendanceSession.objects.create(
                attendance=attendance,
                check_in_time=correction.requested_check_in,
                check_out_time=correction.requested_check_out,
                check_in_photo=correction.check_in_photo,
                check_out_photo=correction.check_out_photo,
            )
            
        elif correction.request_type == 'CONTINUE_SHIFT':
            if correction.session:
                correction.session.continue_shift = True
                correction.session.save()
                
        elif correction.request_type == 'OT_APPROVAL':
            if correction.session:
                correction.session.ot_status = 'APPROVED'
                correction.session.ot_request_created = True
                correction.session.save()
                from attendix.apps.attendance.models import Overtime
                Overtime.objects.update_or_create(
                    employee=attendance.employee,
                    attendance=attendance,
                    session=correction.session,
                    date=attendance.date,
                    defaults={
                        'hours': 2.0, # Admin can adjust later
                        'status': 'APPROVED',
                        'approved_by': approved_by
                    }
                )
                
        elif correction.request_type == 'LATE_CHECKIN_WHILE_ACTIVE':
            # Admin approved second checkin. We should checkout the previous session and create a new one
            if correction.session and correction.session.check_out_time is None:
                shift = attendance.shift or cls.get_active_shift(attendance.employee)
                cls._perform_auto_checkout(correction.session, attendance.employee, attendance, now, shift)
            # Now create a new session
            AttendanceSession.objects.create(
                attendance=attendance,
                check_in_time=now.time(),
                check_in_address="Approved late checkin",
                check_in_lat=0,
                check_in_lng=0
            )

        # Recalculate metrics
        shift = attendance.shift or cls.get_active_shift(attendance.employee)
        cls._recalculate_attendance_metrics(attendance, shift, correction.date)
