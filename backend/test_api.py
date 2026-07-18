import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from attendix.apps.employee.serializers import EmployeeDetailsSerializer
from attendix.apps.employee.models import EmployeeProfile
emp = EmployeeProfile.objects.first()
if emp:
    data = EmployeeDetailsSerializer(emp).data
    print(data.get('shift_start_time'))
