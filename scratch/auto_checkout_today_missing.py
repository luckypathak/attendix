import os
import sys
import django

sys.path.append('/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
django.setup()

from attendix.apps.attendance.services import AttendanceService

if __name__ == '__main__':
    print("Running check_active_overtimes_and_autocheckout...")
    AttendanceService.check_active_overtimes_and_autocheckout()
    print("Finished checking and processing missed checkouts.")
