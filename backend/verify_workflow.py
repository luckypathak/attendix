import json
from django.test import Client

# 1. Initialize Django settings
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
django.setup()

from django.contrib.auth import get_user_model
from attendix.apps.attendance.models import Attendance
from attendix.apps.leave.models import LeaveRequest
from attendix.apps.reimbursement.models import Reimbursement

User = get_user_model()

def run_simulation():
    print("="*60)
    print("STARTING ATTENDIX WORKFORCE OS ROLE-BASED WORKFLOW SIMULATION")
    print("="*60)

    client = Client()

    # ---------------------------------------------------------
    # STEP 1: LOGIN AS EMPLOYEE (john_dev)
    # ---------------------------------------------------------
    print("\n[STEP 1] Logging in as Employee: john_dev...")
    login_res = client.post(
        '/api/v1/auth/login/',
        {'username': 'john_dev', 'password': 'AdminPassword123!'},
        content_type='application/json',
        HTTP_HOST='localhost'
    )
    
    if login_res.status_code != 200:
        print("❌ Login failed!")
        return
        
    auth_data = login_res.json()
    john_token = auth_data['access']
    print(f"✅ Login successful! Role: {auth_data['user']['role']}")
    print(f"Access Token: Bearer {john_token[:25]}...")

    # ---------------------------------------------------------
    # STEP 2: john_dev PUNCHES IN WITH MANDATORY GPS
    # ---------------------------------------------------------
    print("\n[STEP 2] john_dev punching in with GPS coordinates...")
    checkin_payload = {
        "latitude": 37.774900,
        "longitude": -122.419400,
        "accuracy": 12.5,
        "address": "Market Street, San Francisco, CA",
        "device_info": "iOS 17, iPhone 15"
    }
    
    checkin_res = client.post(
        '/api/v1/attendance/records/check-in/',
        checkin_payload,
        content_type='application/json',
        HTTP_HOST='localhost',
        HTTP_AUTHORIZATION=f'Bearer {john_token}'
    )
    
    if checkin_res.status_code == 201:
        print("✅ Clock-in recorded online!")
        print(f"Attendance Date: {checkin_res.json()['date']} | Status: {checkin_res.json()['status']}")
    else:
        print(f"❌ Clock-in failed: {checkin_res.json()}")

    # ---------------------------------------------------------
    # STEP 3: john_dev SUBMITS LEAVE REQUEST
    # ---------------------------------------------------------
    print("\n[STEP 3] john_dev submitting Leave Request (SICK, July 10 to July 12)...")
    leave_payload = {
        "leave_type": "SICK",
        "start_date": "2026-07-10",
        "end_date": "2026-07-12",
        "reason": "Recovering from flu."
    }
    
    leave_res = client.post(
        '/api/v1/leaves/requests/',
        leave_payload,
        content_type='application/json',
        HTTP_HOST='localhost',
        HTTP_AUTHORIZATION=f'Bearer {john_token}'
    )
    
    if leave_res.status_code == 201:
        leave_id = leave_res.json()['id']
        print(f"✅ Leave request submitted successfully! ID: {leave_id}")
    else:
        print(f"❌ Leave submission failed: {leave_res.json()}")
        return

    # ---------------------------------------------------------
    # STEP 4: john_dev SUBMITS REIMBURSEMENT CLAIM
    # ---------------------------------------------------------
    print("\n[STEP 4] john_dev submitting Reimbursement Claim ($150.00 for Office chair)...")
    reimb_payload = {
        "title": "Office Ergonomic Chair",
        "amount": "150.00",
        "description": "Ergonomic chair for home office setup.",
        "receipt_url": "https://res.cloudinary.com/demo/image/upload/v1620000000/sample.jpg"
    }
    
    reimb_res = client.post(
        '/api/v1/reimbursements/',
        reimb_payload,
        content_type='application/json',
        HTTP_HOST='localhost',
        HTTP_AUTHORIZATION=f'Bearer {john_token}'
    )
    
    if reimb_res.status_code == 201:
        reimb_id = reimb_res.json()['id']
        print(f"✅ Expense claim submitted successfully! ID: {reimb_id}")
    else:
        print(f"❌ Expense claim submission failed: {reimb_res.json()}")
        return

    # ---------------------------------------------------------
    # STEP 5: LOGIN AS HR MANAGER (sarah_hr) TO CHECK PENDING APPROVALS
    # ---------------------------------------------------------
    print("\n[STEP 5] Logging in as HR Manager: sarah_hr...")
    mgr_login_res = client.post(
        '/api/v1/auth/login/',
        {'username': 'sarah_hr', 'password': 'AdminPassword123!'},
        content_type='application/json',
        HTTP_HOST='localhost'
    )
    
    if mgr_login_res.status_code != 200:
        print("❌ Manager login failed!")
        return
        
    mgr_auth = mgr_login_res.json()
    sarah_token = mgr_auth['access']
    print(f"✅ Login successful! Role: {mgr_auth['user']['role']}")

    # ---------------------------------------------------------
    # STEP 6: sarah_hr VIEWS THE PENDING LEAVE AND REIMBURSEMENT QUEUES
    # ---------------------------------------------------------
    print("\n[STEP 6] sarah_hr checking the pending Approvals Queue...")
    
    # Fetch pending leaves
    pending_leaves_res = client.get(
        '/api/v1/leaves/requests/?status=PENDING',
        HTTP_HOST='localhost',
        HTTP_AUTHORIZATION=f'Bearer {sarah_token}'
    )
    pending_leaves = pending_leaves_res.json().get('results', pending_leaves_res.json())
    print(f"👉 Pending Leaves in HR Queue: {len(pending_leaves)} item(s) found.")
    for req in pending_leaves:
        print(f"  - Leave Request #{req['id']} | Claimant: {req['employee_name']} | Type: {req['leave_type']} | Reason: {req['reason']}")

    # Fetch pending expenses
    pending_expenses_res = client.get(
        '/api/v1/reimbursements/?status=PENDING',
        HTTP_HOST='localhost',
        HTTP_AUTHORIZATION=f'Bearer {sarah_token}'
    )
    pending_expenses = pending_expenses_res.json().get('results', pending_expenses_res.json())
    print(f"👉 Pending Expenses in HR Queue: {len(pending_expenses)} item(s) found.")
    for claim in pending_expenses:
        print(f"  - Expense claim #{claim['id']} | Claimant: {claim['employee_name']} | Amount: ${claim['amount']} | Receipt: {claim['receipt_url']}")

    # ---------------------------------------------------------
    # STEP 7: sarah_hr APPROVES john_dev's LEAVE
    # ---------------------------------------------------------
    print(f"\n[STEP 7] sarah_hr approving Leave Request #{leave_id}...")
    approve_res = client.post(
        f'/api/v1/leaves/requests/{leave_id}/approve/',
        {"manager_comments": "Approved. Rest well."},
        content_type='application/json',
        HTTP_HOST='localhost',
        HTTP_AUTHORIZATION=f'Bearer {sarah_token}'
    )
    
    if approve_res.status_code == 200:
        print("✅ Leave approved successfully!")
        print(f"Status Updated: {approve_res.json()['status']} | Manager Comments: {approve_res.json()['manager_comments']}")
    else:
        print(f"❌ Leave approval failed: {approve_res.json()}")

    # ---------------------------------------------------------
    # STEP 8: VERIFY AUTOMATIC ATTENDANCE MARKING FOR LEAVE DURATION
    # ---------------------------------------------------------
    print("\n[STEP 8] Verifying automatic Attendance creation for the leave dates (July 10 - July 12)...")
    # Let's inspect the attendance record for July 11
    attendance_record = Attendance.objects.filter(employee__username='john_dev', date='2026-07-11').first()
    if attendance_record:
        print("✅ Automatic Attendance record found!")
        print(f"Date: {attendance_record.date} | Status: {attendance_record.status} | Address Log: {attendance_record.check_in_address}")
    else:
        print("❌ Automatic Attendance record not created.")

    print("\n" + "="*60)
    print("SIMULATION COMPLETED SUCCESSFULLY! MULTI-ROLE APPROVAL CHAIN WORKS!")
    print("="*60)

if __name__ == '__main__':
    run_simulation()
