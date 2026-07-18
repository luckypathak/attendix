import threading
import time
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

def start_background_tasks():
    # Only start once in dev mode (avoid double start with reloader)
    if settings.DEBUG and os.environ.get('RUN_MAIN') != 'true':
        return

    def run_auto_checkout():
        logger.info("Background Auto Checkout thread started. Running every 60s...")
        time.sleep(10) # wait for django to fully boot
        from attendix.apps.attendance.services import AttendanceService
        while True:
            try:
                AttendanceService.check_active_overtimes_and_autocheckout()
            except Exception as e:
                logger.error(f"Auto checkout thread error: {e}")
            time.sleep(60)

    # Start the daemon thread
    thread = threading.Thread(target=run_auto_checkout, daemon=True)
    thread.start()
