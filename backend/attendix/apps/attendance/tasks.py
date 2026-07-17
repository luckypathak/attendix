import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from attendix.apps.attendance.models import Attendance, AttendanceSession

logger = logging.getLogger(__name__)

@shared_task
def cleanup_attendance_photos_task():
    today = timezone.localtime(timezone.now()).date()
    cutoff_date = today - timedelta(days=2)
    logger.info(f"Starting scheduled photo cleanup task. Cutoff date: {cutoff_date}")

    parent_records = Attendance.objects.filter(date__lte=cutoff_date)
    parent_count = 0
    for att in parent_records:
        if att.captured_image:
            try:
                att.captured_image.delete(save=True)
                parent_count += 1
            except Exception as e:
                logger.error(f"Error deleting parent photo for ID {att.id}: {e}")

    sessions = AttendanceSession.objects.filter(attendance__date__lte=cutoff_date)
    session_in_count = 0
    session_out_count = 0
    for sess in sessions:
        if sess.captured_image:
            try:
                sess.captured_image.delete(save=True)
                session_in_count += 1
            except Exception as e:
                logger.error(f"Error deleting check-in photo for session {sess.id}: {e}")
        if sess.check_out_captured_image:
            try:
                sess.check_out_captured_image.delete(save=True)
                session_out_count += 1
            except Exception as e:
                logger.error(f"Error deleting check-out photo for session {sess.id}: {e}")

    msg = f"Cleanup completed. Deleted {parent_count} parent photos, {session_in_count} session check-in photos, {session_out_count} session check-out photos."
    logger.info(msg)
    return msg


@shared_task
def check_active_overtimes_task():
    logger.info("Starting active overtime and auto checkout background task.")
    from attendix.apps.attendance.services import AttendanceService
    AttendanceService.check_active_overtimes_and_autocheckout()
    logger.info("Active overtime and auto checkout check completed.")
    return "Check completed."

