import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

import traceback

try:
    from attendix.apps.attendance.models import Attendance, Overtime, AttendanceSession
    from attendix.apps.leave.models import LeaveRequest, LeaveBalance
    from attendix.apps.payroll.models import Payroll, PayrollBranchBreakdown, AdvanceSalary
    from attendix.apps.reimbursement.models import Reimbursement
    from attendix.apps.todo.models import Todo
    from attendix.apps.employee.models import EmployeeFirmAllocation
    from attendix.apps.notifications.models import Notification
    print("All models imported successfully!")
except Exception as e:
    traceback.print_exc()

