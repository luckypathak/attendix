import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from attendix.apps.employee.models import EmployeeProfile
from attendix.apps.employee.serializers import EmployeeDetailsSerializer
emp = EmployeeProfile.objects.first()
print(EmployeeDetailsSerializer(emp).data.keys())
