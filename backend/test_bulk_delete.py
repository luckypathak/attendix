import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

import traceback
from django.contrib.auth import get_user_model
User = get_user_model()
a1 = User.objects.filter(username='a1').first()
if a1 and hasattr(a1, 'employee_profile'):
    print(f"Deleting {a1.username}...")
    try:
        from rest_framework.test import APIRequestFactory
        from attendix.apps.employee.views import EmployeeViewSet
        from rest_framework.test import force_authenticate
        factory = APIRequestFactory()
        request = factory.post('/employees/bulk-delete/', {'employee_ids': [a1.employee_profile.id]}, format='json')
        user = User.objects.filter(is_superuser=True).first()
        force_authenticate(request, user=user)
        view = EmployeeViewSet.as_view({'post': 'bulk_delete'})
        response = view(request)
        print("Response:", response.status_code, response.data)
    except Exception as e:
        traceback.print_exc()
else:
    print("No employee a1 found")
