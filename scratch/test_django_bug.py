import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
from attendix.apps.attendance.models import AttendanceSession
import json

User = get_user_model()
c = Client()
admin = User.objects.filter(role="SUPER_ADMIN").first()
sess = AttendanceSession.objects.first()

c.force_login(admin)
try:
    resp = c.patch(
        "/api/attendance/records/edit-session/",
        json.dumps({"session_id": sess.id, "reason": "test", "check_in_time": "10:00"}),
        content_type="application/json",
        SERVER_NAME="localhost"
    )
    print("STATUS", resp.status_code)
except Exception as e:
    import traceback
    traceback.print_exc()
