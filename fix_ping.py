import re

with open('backend/attendix/apps/attendance/views.py', 'r') as f:
    content = f.read()

# Replace the ping logic
old_logic = """        if work_category == 'FIELD':
            from .models import LocationPing
            LocationPing.objects.create(
                session=session,
                latitude=latitude,
                longitude=longitude,
                speed=speed,
                accuracy=accuracy
            )
            return Response({"detail": "Location ping saved."}, status=status.HTTP_200_OK)
        else:
            # OFFICE STAFF logic"""

new_logic = """        # ALL STAFF MUST BE TRACKED IN DB
        from .models import LocationPing
        LocationPing.objects.create(
            session=session,
            latitude=latitude,
            longitude=longitude,
            speed=speed,
            accuracy=accuracy
        )
        
        if work_category == 'FIELD':
            return Response({"detail": "Location ping saved."}, status=status.HTTP_200_OK)
        else:
            # OFFICE STAFF logic"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open('backend/attendix/apps/attendance/views.py', 'w') as f:
        f.write(content)
    print("Fixed ping logic successfully.")
else:
    print("Could not find the old ping logic.")

