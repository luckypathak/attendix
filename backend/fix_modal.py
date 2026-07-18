import re

with open("../frontend/src/components/EditAttendanceModal.jsx", "r") as f:
    content = f.read()

# Add employee name to the modal title
old_title = "<DialogTitle sx={{ fontWeight: 700 }}>Edit Attendance Session</DialogTitle>"
new_title = "<DialogTitle sx={{ fontWeight: 700 }}>Edit Attendance: {session?.employee_name || 'Session'}</DialogTitle>"

content = content.replace(old_title, new_title)

with open("../frontend/src/components/EditAttendanceModal.jsx", "w") as f:
    f.write(content)

