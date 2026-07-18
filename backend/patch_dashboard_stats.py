import re

with open("../backend/attendix/apps/company/views.py", "r") as f:
    content = f.read()

# Fix the AuditLog query
old_log = "log = AttendanceAuditLog.objects.filter(session=session).first()"
new_log = "log = AttendanceAuditLog.objects.filter(session=session).order_by('-created_at').first()"
content = content.replace(old_log, new_log)

with open("../backend/attendix/apps/company/views.py", "w") as f:
    f.write(content)
