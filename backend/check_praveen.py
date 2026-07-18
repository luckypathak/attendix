import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
for u in User.objects.all():
    print(u.username)
