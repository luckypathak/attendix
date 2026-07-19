import logging
import math
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import datetime
from django.db import connection
from attendix.apps.attendance.models import Attendance, AttendanceSession, LocationPing, AttendanceCorrectionRequest
from attendix.apps.authentication.models import User
from attendix.apps.notifications.services import NotificationService

logger = logging.getLogger(__name__)

# Utility for Haversine distance
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000 # Earth radius in meters
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@shared_task(bind=True, max_retries=3)
def check_active_overtimes_task(self):
    """1. Auto Checkout Engine: Every minute"""
    logger.info("Starting Auto Checkout Engine.")
    from attendix.apps.attendance.services import AttendanceService
    AttendanceService.check_active_overtimes_and_autocheckout()
    return "Check completed."

@shared_task(bind=True, max_retries=3)
def location_tracker_task(self):
    """2. Location Tracker: Every 5 minutes"""
    logger.info("Starting Location Tracker.")
    now = timezone.localtime(timezone.now())
    active_sessions = AttendanceSession.objects.filter(check_out_time__isnull=True).select_related('attendance__employee__company')
    
    for session in active_sessions:
        employee = session.attendance.employee
        company = employee.company
        if not company or not company.latitude or not company.longitude:
            continue
            
        last_ping = session.location_pings.order_by('-timestamp').first()
        if last_ping:
            # Check for office staff geofence out
            if getattr(employee.employee_profile, 'work_type', 'OFFICE') == 'OFFICE':
                distance = calculate_distance(last_ping.latitude, last_ping.longitude, company.latitude, company.longitude)
                office_radius = company.office_radius_meters if company.office_radius_meters else 100
                if distance > office_radius:
                    grace_period_mins = company.geofence_grace_period_minutes if company.geofence_grace_period_minutes else 5
                    out_duration = (now - last_ping.timestamp).total_seconds() / 60
                    if out_duration >= grace_period_mins:
                        # Auto checkout
                        session.check_out_time = now.time()
                        session.auto_checkout = True
                        session.checkout_reason = 'LEFT_OFFICE_GEOFENCE'
                        session.save()
                        session.attendance.check_out_time = session.check_out_time
                        session.attendance.save()
                        
                        from attendix.apps.attendance.services import AttendanceService
                        shift = session.attendance.shift or getattr(employee.employee_profile, 'shift', None)
                        AttendanceService._recalculate_attendance_metrics(session.attendance, shift, now.date())
                        logger.info(f"Auto-checked out {employee.username} due to geofence.")
    return "Location tracking complete."

@shared_task(bind=True, max_retries=3)
def attendance_status_recalculation_task(self):
    """3. Attendance Status Recalculation: Every 15 minutes"""
    logger.info("Recalculating attendance metrics.")
    from attendix.apps.attendance.services import AttendanceService
    today = timezone.localtime(timezone.now()).date()
    active_att = Attendance.objects.filter(date=today, sessions__check_out_time__isnull=True).distinct()
    for att in active_att:
        shift = att.shift or getattr(att.employee.employee_profile, 'shift', None)
        if shift:
            AttendanceService._recalculate_attendance_metrics(att, shift, today)
    return f"Recalculated {active_att.count()} attendances."

@shared_task(bind=True, max_retries=3)
def auto_absent_marker_task(self):
    """4. Auto Absent Marker: Every 30 minutes"""
    logger.info("Starting Auto Absent Marker.")
    now = timezone.localtime(timezone.now())
    today = now.date()
    
    # Do not mark ABSENT on Sundays (weekday() == 6)
    if today.weekday() == 6:
        logger.info("Today is Sunday. Skipping auto absent marker.")
        return "Skipped (Sunday)"
    
    # Simple logic: users without attendance today, whose shift started > 30 mins ago
    from attendix.apps.employee.models import EmployeeProfile
    profiles = EmployeeProfile.objects.exclude(user__attendance_records__date=today).exclude(user__leaves__start_date__lte=today, user__leaves__end_date__gte=today, user__leaves__status='APPROVED').select_related('shift', 'user')
    
    marked = 0
    for profile in profiles:
        shift = profile.shift
        if shift and shift.end_time:
            shift_end = datetime.datetime.combine(today, shift.end_time)
            shift_end = timezone.make_aware(shift_end, timezone.get_current_timezone())
            if now > shift_end:
                Attendance.objects.create(employee=profile.user, date=today, status='ABSENT')
                marked += 1
    return f"Marked {marked} employees as ABSENT."

@shared_task(bind=True, max_retries=3)
def pending_ot_reminder_task(self):
    """5. Pending OT Reminder: Every 10 minutes"""
    logger.info("Starting Pending OT Reminder.")
    pending = AttendanceCorrectionRequest.objects.filter(status='PENDING', request_type__in=['CONTINUE_SHIFT', 'OT_APPROVAL'])
    for req in pending:
        # Notify admins again if it's getting old
        admins = User.objects.filter(company=req.employee.company, role__in=['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER'])
        for admin in admins:
            NotificationService.create_in_app_notification(
                recipient=admin,
                title="Pending Request Reminder",
                body=f"Reminder: {req.employee.username} has a pending {req.get_request_type_display()} request waiting for approval."
            )
    return f"Sent reminders for {pending.count()} requests."

@shared_task(bind=True, max_retries=3)
def analytics_refresh_task(self):
    """6. Analytics Refresh: Every 15 minutes"""
    logger.info("Refreshing Analytics Cache.")
    # Here we would bust the dashboard cache, if we use one
    return "Analytics refreshed."

@shared_task(bind=True, max_retries=3)
def payroll_sync_task(self):
    """7. Payroll Sync: Nightly"""
    logger.info("Starting Nightly Payroll Sync.")
    # Add real payroll logic here when built
    return "Payroll sync complete."

@shared_task(bind=True, max_retries=3)
def cleanup_expired_requests_task(self):
    """8. Cleanup Expired Requests: Daily"""
    logger.info("Cleaning up expired requests.")
    cutoff = timezone.localtime(timezone.now()) - timedelta(days=7)
    expired = AttendanceCorrectionRequest.objects.filter(status='PENDING', created_at__lte=cutoff)
    count = expired.count()
    expired.update(status='REJECTED', rejected_reason='AUTO REJECTED (Expired)')
    return f"Cleaned up {count} expired requests."

@shared_task(bind=True, max_retries=3)
def database_health_check_task(self):
    """9. Database Health Check: Hourly"""
    logger.info("Checking DB Health.")
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
    return "DB Health OK."

@shared_task(bind=True, max_retries=3)
def missed_checkout_reconciliation_task(self):
    """10. Missed Checkout Reconciliation: Daily"""
    logger.info("Reconciling missed checkouts.")
    today = timezone.localtime(timezone.now()).date()
    missed = AttendanceSession.objects.filter(check_out_time__isnull=True, attendance__date__lt=today)
    count = missed.count()
    from django.db.models import F
    for session in missed:
        profile = getattr(session.attendance.employee, 'employee_profile', None)
        if profile:
            profile.checkout_missed_count = F('checkout_missed_count') + 1
            profile.save(update_fields=['checkout_missed_count'])
        session.check_out_time = datetime.time(23, 59, 59)
        session.auto_checkout = True
        session.checkout_reason = 'AUTO_CHECKOUT_RECONCILIATION'
        session.save()
    return f"Reconciled {count} missed sessions."

@shared_task(bind=True, max_retries=3)
def cleanup_attendance_photos_task(self):
    today = timezone.localtime(timezone.now()).date()
    cutoff_date = today - timedelta(days=2)
    
    parent_records = Attendance.objects.filter(date__lte=cutoff_date).exclude(captured_image='')
    for att in parent_records:
        att.captured_image.delete(save=True)
    return "Cleanup photos done."

