import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from attendix.apps.employee.serializers import EmployeeDetailsSerializer
from attendix.apps.employee.models import EmployeeProfile
for emp in EmployeeProfile.objects.all():
    data = EmployeeDetailsSerializer(emp).data
    if data.get('shift_start_time'):
        print(emp.user.username, data.get('shift_start_time'), data.get('shift_name'))
