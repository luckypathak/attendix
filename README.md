# Attendix Workforce OS

Attendix Workforce OS is a production-grade, multi-company ready, SaaS-ready Workforce Management and HRMS platform. It features a Django 5 REST backend, a responsive React + Material UI portal, a React Native offline-sync mobile app, and a custom Android dual-SIM SMS Gateway.

---

## 🏗 Technology Stack

- **Backend**: Django 5, Django REST Framework, SimpleJWT (Authentication), Celery (Background workers), Redis (Broker).
- **Database**: PostgreSQL (Multi-tenant ready, soft-deletes).
- **Frontend**: React + Vite, Redux Toolkit (State Management), Material UI (Theme & CSS system).
- **Mobile**: React Native (Geolocation API, AsyncStorage offline caching, background synchronization).
- **Orchestration**: Docker, Docker Compose.

---

## 📁 Workspace Directory Structure

```
attendix-workforce-os/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/                  # Django 5 Backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── attendix/
│       ├── settings.py
│       └── apps/             # Modular Django Apps
│           ├── authentication/
│           ├── company/
│           ├── employee/
│           ├── attendance/
│           ├── leave/
│           ├── payroll/
│           ├── reimbursement/
│           ├── todo/
│           ├── notifications/
│           └── audit/
├── frontend/                 # React Vite Portal
│   ├── Dockerfile
│   ├── package.json
│   └── src/
└── mobile/                   # React Native Mobile App
    ├── package.json
    ├── App.js
    └── src/
```

---

## ⚙️ Core Business & Attendance Rules

### 1. Mandatory Geolocation Checking
- All clock-in/out records must submit coordinate parameters (`latitude`, `longitude`, `accuracy`, `address`).
- If location services are turned off or permissions are denied on the handset, check-ins are blocked.
- Locations with poor GPS accuracy (> 50 meters) are blocked.
- Manual coordinates insertion or cached GPS checks are strictly forbidden.

### 2. Shift Grace Periods & Late Arrivals
- Every company has a configurable shift start-time (e.g. 09:00 AM) and grace period (default 15 minutes).
- Check-ins after the grace period (e.g. 09:16 AM onwards) are flagged as `LATE`.
- **4th Late Warning Rule**: If an employee accumulates 3 late arrivals in a calendar month, the 4th late check-in automatically marks their attendance status as `HALF_DAY`, resulting in a half-day pay deduction.

### 3. Automated Check-out & Reminders
- If an employee forgets to clock out, the system triggers a check-out reminder alert after 1 hour.
- If no approved Overtime (OT) is recorded, the system automatically checks the user out after a configurable grace period (e.g. 10 hours from clock-in) and writes a system flag: `SYSTEM AUTO CHECKOUT (Forgotten checkout)`.

### 4. Paid Holidays & Absences
- Approved leaves automatically write `Attendance` entries with status `LEAVE` for those dates.
- Days with no attendance log and no approved leaves are marked as `ABSENT`.
- Monthly payroll is calculated based on the actual month days (28, 29, 30, or 31). Unpaid leaves and absent days trigger salary deductions: `deduction = (base_salary / days_in_month) * deduction_days`.
- Confirmed company holidays are paid.

### 5. Advance Salary Deductions
- Approved salary advances with repayment terms are automatically deducted from the employee's monthly payslip during payroll generation, capped at the monthly repayment limit.

---

## 📡 Android SMS Gateway & SIM Failover

Attendix features a built-in Android SMS Gateway API. It uses physical Android handsets as gateway nodes:
1. The Android gateway app polls the `/api/v1/notifications/gateway/poll/?device_id=...` API.
2. The backend filters pending SMS alerts in the queue and assigns them a SIM slot (SIM 1 or SIM 2) based on daily sending limits.
3. If SIM 1 reaches its daily limit (e.g., 100 SMS/day), future messages automatically route to SIM 2.
4. The handset sends the SMS via native Android dual-SIM managers and reports the status back to `/api/v1/notifications/gateway/status/`, which updates the daily counters.

---

## 🔐 Database Schema & Relationships (ERD)

The database schema is fully normalized. Below are the key tables and constraints:

- **`company_company`**: IDs, settings (grace periods, SIM limits, auto-checkout).
- **`company_department`**: Linked to `company_company` (FK). Name, description.
- **`company_designation`**: Linked to `company_company` (FK). Name, description.
- **`authentication_user`**: Custom User model. Role choices: `SUPER_ADMIN`, `COMPANY_ADMIN`, `MANAGER`, `EMPLOYEE`. Linked to `company_company` (FK, nullable).
- **`employee_employeeprofile`**: One-to-One with `authentication_user`. Linked to `company_department` (FK), `company_designation` (FK), and reporting `manager` (FK to `authentication_user`). Holds basic salary, hourly rates, bank details, and joining dates.
- **`attendance_shift`**: Linked to `company_company` (FK). Holds shift times.
- **`attendance_attendance`**: Linked to `authentication_user` (FK). Tracks check-in/out times, statuses, check-in and check-out GPS details (coordinates, accuracy, device info). Unique constraint: `(employee_id, date)`.
- **`attendance_overtime`**: One-to-One with `attendance_attendance`. Holds OT hours and approval states.
- **`leave_leaverequest`**: Linked to `authentication_user` (FK) and `approved_by` (FK). Tracks leave types, start/end dates, reason, and approval comments.
- **`leave_leavebalance`**: Linked to `authentication_user` (FK). Unique constraint: `(employee_id, leave_type)`. Tracks allocated vs used leaves.
- **`leave_holiday`**: Linked to `company_company` (FK). Tracks paid company holidays.
- **`payroll_advancesalary`**: Linked to `authentication_user` (FK). Tracks advance amount, repayments, and deduction rules.
- **`payroll_payroll`**: Linked to `authentication_user` (FK). Tracks monthly payslip breakdowns, gross, deductions, and net salary. Unique constraint: `(employee_id, month, year)`.
- **`notifications_notification`**: Linked to `authentication_user` (FK). Tracks FCM pushes and alert feeds.
- **`notifications_smsqueue`**: Tracks pending SMS logs.
- **`notifications_smsgatewaydevice`**: Tracks registered Android devices and SIM counts.
- **`audit_auditlog`**: Linked to `authentication_user` (FK, nullable). Tracks model name, primary key, action (CREATE/UPDATE/DELETE), IP address, and JSON changes.

---

## 🚀 Running the Project Locally

### Prerequisites
- Install **Docker** and **Docker Compose**.
- Alternatively, install **Python 3.11** and **Node.js (v18+)** locally.

### Running with Docker Compose (Recommended)
1. Copy the environment file template:
   ```bash
   cp .env.example .env
   ```
2. Build and run all services in the background:
   ```bash
   docker-compose up --build -d
   ```
3. Run database migrations:
   ```bash
   docker-compose exec backend python manage.py migrate
   ```
4. Seed demo data (creates organizations, engineers, managers, shifts, and check-in histories):
   ```bash
   docker-compose exec backend python manage.py seed_data
   ```

### Live API Documentation
- Access the auto-generated Swagger UI at: [http://localhost:8000/api/v1/docs/](http://localhost:8000/api/v1/docs/)
- The OpenAPI JSON scheme is fetched at `/api/schema/`.

### Accessing the Portals
- **React Admin/Employee Frontend**: Open [http://localhost:5173/](http://localhost:5173/)
- **Superadmin User**: `superadmin` / `AdminPassword123!`
- **Company Admin User**: `attendix_admin` / `AdminPassword123!`
- **HR Manager User**: `sarah_hr` / `AdminPassword123!`
- **Employee User**: `john_dev` / `AdminPassword123!`

---

## 🧪 Testing

To run the complete backend testing suite validating attendance rules, GPS validations, and payroll calculations:
```bash
# Inside docker
docker-compose exec backend python manage.py test

# Running locally
cd backend
python manage.py test
```

---

## 🌐 Production Deployment Guide

1. **Database**: Provision a PostgreSQL instance using **Neon DB** or **Supabase**. Inject connection details into `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
2. **Caching & Workers**: Set up a serverless Redis instance on **Upstash**. Set `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`.
3. **Backend Service**: Deploy the `backend` Dockerfile to **Railway** or **Render**. Ensure environment variables from `.env` are configured. Add a celery beat task cron-job to run `AttendanceService.process_auto_checkout()` daily at midnight.
4. **Media Store**: Configure Cloudinary credentials (`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`) to enable receipt attachment uploads.
5. **Frontend Web**: Build the React bundle (`npm run build` in the frontend directory) and deploy to **Vercel**. Set `VITE_API_URL` pointing to the deployed backend server.
