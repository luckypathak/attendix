import os, sys, django
from dotenv import load_dotenv
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.create(username='softdelete_test_user')
from attendix.apps.employee.models import EmployeeProfile
p = EmployeeProfile.objects.create(user=u, base_salary=1000)

print(f"Before delete: {EmployeeProfile.objects.filter(id=p.id).exists()}")
u.delete()
p.delete()
print(f"After delete: {EmployeeProfile.objects.filter(id=p.id).exists()}")
print(f"User is_deleted: {User.objects.filter(id=u.id).first().is_deleted}")
print(f"User is_active: {User.objects.filter(id=u.id).first().is_active}")

