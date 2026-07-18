import os, sys, django
from dotenv import load_dotenv
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
load_dotenv(os.path.join("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend", ".env"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

import traceback
from django.contrib.auth import get_user_model
User = get_user_model()

u = User.objects.filter(username='a1').first()
if u and hasattr(u, 'employee_profile'):
    print(f"Deleting {u.username}...")
    try:
        from rest_framework.test import APIRequestFactory
        from attendix.apps.employee.views import EmployeeViewSet
        from rest_framework.test import force_authenticate
        factory = APIRequestFactory()
        request = factory.delete(f'/employees/{u.employee_profile.id}/')
        user = User.objects.filter(is_superuser=True).first()
        force_authenticate(request, user=user)
        view = EmployeeViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=u.employee_profile.id)
        print("Response:", response.status_code, getattr(response, 'data', None))
    except Exception as e:
        traceback.print_exc()
else:
    print("No employee a1 found")
