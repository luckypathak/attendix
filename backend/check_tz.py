import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from django.utils import timezone
import datetime

tz = timezone.get_current_timezone()
now_dt = timezone.localtime(timezone.now())
created_at_utc = timezone.now()

diff = (now_dt - created_at_utc).total_seconds()
print("Diff:", diff)
