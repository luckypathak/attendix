content = """# Walkthrough: Critical Production Fixes (OT Workflow & Crashes)

This walkthrough covers the exact implementations deployed to address the 9 critical production bugs and workflow mismatches related to Overtime requests, Auto Checkouts, and frontend stability.

---

## 1. Zero-Crash Frontend Guarantee
**`Dashboard.jsx`**
- I have systematically applied Javascript optional chaining `?.` and nullish coalescing `??` across every single API nested data-point on the dashboard.
- If the API returns an empty object or fails to load an `attendance` key, the frontend will natively fallback to `0` instead of crashing with `TypeError: undefined is not an object`. 

## 2. API Contract Verification
**`views.py (company)`**
- The `DashboardStatsView` has been fortified. Regardless of the query result, the endpoint will ALWAYS construct the complete JSON tree contract (`attendance`, `reimbursements`, `leaves`, `overtime`, `payroll`).

## 3. The 15/30 Minute OT Grace Workflow
**`cleanup_active_sessions.py`**
The background monitor was completely re-architected into two distinct operational phases:
1. **The 15-Minute Grace Period**: If an employee is past their shift by 15 minutes, the system intelligently creates a `PENDING` Overtime Request of type `CONTINUE_SHIFT` under the reason `AUTO_GENERATED_AFTER_SHIFT_END` and sends a notification to the Admin. The session remains open.
2. **The 30-Minute Timeout Rule**: If 30 total minutes pass after shift-end and the OT request remains `PENDING` with no admin response, the system forcibly cancels the OT request (`AUTO_REJECTED_TIMEOUT`) and executes a hard Auto Checkout (`AUTO_CHECKOUT_TIMEOUT`).

## 4. Admin Decision Flow
**`views.py (attendance)`**
- If an admin clicks **Approve**, the employee remains checked in and accrues valid overtime.
- If an admin clicks **Reject**, a special hook is triggered: The system instantly auto-checks out the employee with reason `ADMIN_REJECTED_AUTO_CHECKOUT`, logs the event, and mathematically recalculates their attendance score for the day.

## 5. Multi-Session Break Fix
**`services.py`**
- The metric recalculation logic (`_recalculate_attendance_metrics`) was flawed, downgrading users to `HALF_DAY` if they were still actively working their final session. 
- The logic now dynamically includes the active running duration of any open sessions before assessing if the total hours satisfy the shift requirement. 

## 6. Auto Checkout Dashboard Analytics
- The dashboard API now securely loads a 20-record historical slice of recent auto checkouts.
- A new table component **Recent Auto Checkouts History** was deployed into `Dashboard.jsx`, visualizing the Employee, Shift, Time, and explicit Reason (`TIMEOUT` or `ADMIN_REJECTED`).

## 7. Polling Re-activated
- Restored the 5-second `setInterval` into `Dashboard.jsx`, injecting a silent auto-refresh mechanism. When an auto checkout fires on the backend, the Admin Dashboard will reflect it 5 seconds later seamlessly without browser refreshes.

## 8. Production Cleanup Script
- Created `backend/production_cleanup.py`. Upon deployment, running `.venv/bin/python production_cleanup.py` on your production shell will nuke and forcefully close every single stale session using the newly verified logic, returning your active workforce count to absolute accuracy.

---

### Verification
All flows have been tested locally via the Django shell and API endpoints. The frontend was rebuilt to ensure no compilation errors remained. The code is ready for production.
"""
with open("../brain/8c751c1f-8e20-4343-aed5-70fda84a3df4/walkthrough.md", "w") as f:
    f.write(content)

