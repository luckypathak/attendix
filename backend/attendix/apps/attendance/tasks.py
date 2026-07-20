import logging
import math
import datetime
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.db import connection
from django.db.models import F
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
def dynamic_auto_checkout_task(self, session_id):
    """Dynamic Auto Checkout Engine: Runs at exact expected shift end + grace period"""
    logger.info(f"Running dynamic auto checkout for session {session_id}")
    try:
        session = AttendanceSession.objects.get(id=session_id)
    except AttendanceSession.DoesNotExist:
        return "Session not found."
        
    if session.check_out_time is not None:
        return "Already checked out."
        
    # Check out the user
    now = timezone.localtime(timezone.now())
    
    # We must auto checkout at the EXACT shift end, NOT the grace period time.
    from attendix.apps.attendance.services import AttendanceService
    AttendanceService.perform_auto_checkout(session)
    return "Dynamic Auto-checkout performed."

@shared_task(bind=True, max_retries=3)
def location_tracker_task(self):
    """Location Tracker: Dynamic (Only runs if active sessions exist)"""
    logger.info("Starting Location Tracker.")
    active_sessions = AttendanceSession.objects.filter(check_out_time__isnull=True).select_related('attendance__employee__company')
    
    if not active_sessions.exists():
        return "Skipped (No active users checked in)"
        
    now = timezone.localtime(timezone.now())
    
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
                        from attendix.apps.attendance.services import AttendanceService
                        AttendanceService.perform_auto_checkout(session, reason='LEFT_OFFICE_GEOFENCE')
                        logger.info(f"Auto-checked out {employee.username} due to geofence.")
    return "Location tracking complete."

@shared_task(bind=True, max_retries=3)
def auto_absent_marker_task(self):
    """Auto Absent Marker: Runs ONCE daily at Midnight (00:00)"""
    logger.info("Starting Auto Absent Marker.")
    now = timezone.localtime(timezone.now())
    today = now.date() - timedelta(days=1) # Because it runs at midnight, we check for YESTERDAY
    
    # Do not mark ABSENT on Sundays (if yesterday was Sunday)
    if today.weekday() == 6:
        logger.info("Yesterday was Sunday. Skipping auto absent marker.")
        return "Skipped (Sunday)"
    
    from attendix.apps.employee.models import EmployeeProfile
    profiles = EmployeeProfile.objects.exclude(user__attendance_records__date=today).exclude(user__leaves__start_date__lte=today, user__leaves__end_date__gte=today, user__leaves__status='APPROVED').select_related('shift', 'user')
    
    marked = 0
    for profile in profiles:
        Attendance.objects.create(employee=profile.user, date=today, status='ABSENT')
        marked += 1
    return f"Marked {marked} employees as ABSENT for {today}."

@shared_task(bind=True, max_retries=3)
def cleanup_expired_requests_task(self):
    """Cleanup Expired Requests: Daily"""
    logger.info("Cleaning up expired requests.")
    cutoff = timezone.localtime(timezone.now()) - timedelta(days=7)
    expired = AttendanceCorrectionRequest.objects.filter(status='PENDING', created_at__lte=cutoff)
    count = expired.count()
    expired.update(status='REJECTED', rejected_reason='AUTO REJECTED (Expired)')
    return f"Cleaned up {count} expired requests."

@shared_task(bind=True, max_retries=3)
def cleanup_attendance_photos_task(self):
    """Cleanup Attendance Photos: Daily"""
    today = timezone.localtime(timezone.now()).date()
    cutoff_date = today - timedelta(days=2)
    
    parent_records = Attendance.objects.filter(date__lte=cutoff_date).exclude(captured_image='')
    for att in parent_records:
        att.captured_image.delete(save=True)
    return "Cleanup photos done."
