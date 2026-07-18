import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from attendix.apps.attendance.services import AttendanceService
from attendix.apps.attendance.models import AttendanceSession, Attendance, AttendanceCorrectionRequest
from django.utils import timezone
import datetime
from django.contrib.auth import get_user_model

User = get_user_model()
u = User.objects.filter(username='bulk_delete_test').first()
if not u:
    print("User bulk_delete_test not found")
else:
    # Set up dummy session for bulk_delete_test
    AttendanceSession.objects.filter(attendance__employee=u).delete()
    AttendanceCorrectionRequest.objects.filter(employee=u).delete()

    att, _ = Attendance.objects.get_or_create(employee=u, date=timezone.now().date(), defaults={'status': 'PRESENT'})
    att.sessions.all().delete()

    session = AttendanceSession.objects.create(
        attendance=att,
        check_in_time=datetime.time(10, 0),
        status='ACTIVE'
    )
    # create shift that ended 20 minutes ago
    print("User is active. Running first pass (should create pending request)...")
    
    # Mock shift via a class or mock
    class MockShift:
        start_time = datetime.time(9, 0)
        end_time = (timezone.now() - datetime.timedelta(minutes=20)).time()
        name = "Mock"
    
    u.employee_profile.shift = MockShift()

    # Try running the actual service logic
    # Actually wait, shift is tied to DB. Let's just create a real shift.
