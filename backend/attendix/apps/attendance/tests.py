import datetime
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from attendix.apps.company.models import Company, Department, Designation
from attendix.apps.attendance.models import Shift, Attendance, Overtime
from attendix.apps.employee.models import EmployeeProfile
from attendix.apps.attendance.services import AttendanceService
from attendix.apps.payroll.services import PayrollService
from attendix.apps.payroll.models import Payroll, AdvanceSalary

User = get_user_model()


class AttendanceRulesTests(TestCase):
    def setUp(self):
        # 1. Create Company
        self.company = Company.objects.create(
            name='Test Corp',
            domain='test.com',
            grace_period_minutes=15,
            late_limit_for_half_day=3
        )
        
        # 2. Create Shift (9 AM - 6 PM)
        self.shift = Shift.objects.create(
            company=self.company,
            name='Test Shift',
            start_time=datetime.time(9, 0, 0),
            end_time=datetime.time(18, 0, 0),
            grace_period_minutes=15
        )

        # 3. Create User
        self.user = User.objects.create_user(
            username='developer_one',
            email='dev1@test.com',
            password='TestPassword123!',
            company=self.company,
            role=User.Roles.EMPLOYEE
        )

        # 4. Create Employee Profile
        self.profile = EmployeeProfile.objects.create(
            user=self.user,
            base_salary=6000.00,
            hourly_rate=35.00,
            joining_date=datetime.date(2026, 1, 1)
        )

    def test_check_in_requires_gps(self):
        """GPS coordinates should be mandatory for check-in."""
        with self.assertRaises(ValidationError):
            AttendanceService.check_in(
                employee=self.user,
                lat=None,
                lng=None,
                accuracy=10.0,
                address='',
                device_info='Test Device'
            )

    def test_check_in_poor_gps_accuracy_blocked(self):
        """Poor GPS accuracy (> 50m) should block check-in."""
        with self.assertRaises(ValidationError):
            AttendanceService.check_in(
                employee=self.user,
                lat=37.774900,
                lng=-122.419400,
                accuracy=85.0, # 85 meters (exceeds 50m limit)
                address='Market St',
                device_info='Test Device'
            )

    def test_check_in_grace_period(self):
        """Check-in within grace period should be PRESENT, after grace should be LATE."""
        # Case A: On time (09:05 AM - within 15 mins)
        timestamp_on_time = timezone.make_aware(
            datetime.datetime(2026, 7, 6, 9, 5, 0)
        )
        rec1 = AttendanceService.check_in(
            employee=self.user,
            lat=37.774900,
            lng=-122.419400,
            accuracy=10.0,
            address='Market St',
            device_info='Test Device',
            timestamp=timestamp_on_time
        )
        self.assertEqual(rec1.status, Attendance.Statuses.PRESENT)

        # Clear check-in for next assertion (Hard-delete to bypass unique index constraints)
        Attendance.all_objects.filter(id=rec1.id).delete()

        # Case B: Late (09:20 AM - exceeds 15 mins grace period)
        timestamp_late = timezone.make_aware(
            datetime.datetime(2026, 7, 6, 9, 20, 0)
        )
        rec2 = AttendanceService.check_in(
            employee=self.user,
            lat=37.774900,
            lng=-122.419400,
            accuracy=10.0,
            address='Market St',
            device_info='Test Device',
            timestamp=timestamp_late
        )
        self.assertEqual(rec2.status, Attendance.Statuses.LATE)

    def test_fourth_late_becomes_half_day(self):
        """After 3 late arrivals in a month, the next late check-in automatically becomes a Half Day."""
        # Seed 3 late attendances
        for day in range(1, 4):
            Attendance.objects.create(
                employee=self.user,
                shift=self.shift,
                date=datetime.date(2026, 7, day),
                check_in_time=datetime.time(9, 25, 0),
                status=Attendance.Statuses.LATE,
                check_in_lat=37.774900,
                check_in_lng=-122.419400
            )

        # Attempt the 4th check-in which is also late (09:30 AM)
        timestamp_fourth_late = timezone.make_aware(
            datetime.datetime(2026, 7, 4, 9, 30, 0)
        )
        rec = AttendanceService.check_in(
            employee=self.user,
            lat=37.774900,
            lng=-122.419400,
            accuracy=12.0,
            address='Market St',
            device_info='Test Device',
            timestamp=timestamp_fourth_late
        )
        
        # Should resolve as HALF_DAY because limit (3) was exceeded
        self.assertEqual(rec.status, Attendance.Statuses.HALF_DAY)

    def test_payroll_calculation_days_in_month(self):
        """Verify payroll calculation handles calendar length and absent deductions correctly."""
        # For July 2026 (31 days)
        # Seed 1 checked-in day, 0 leaves. Remaining 30 days are ABSENT.
        Attendance.objects.create(
            employee=self.user,
            shift=self.shift,
            date=datetime.date(2026, 7, 1),
            check_in_time=datetime.time(9, 0, 0),
            check_out_time=datetime.time(18, 0, 0),
            status=Attendance.Statuses.PRESENT,
            check_in_lat=37.774900,
            check_in_lng=-122.419400
        )

        payroll = PayrollService.generate_monthly_payroll(
            employee=self.user,
            month=7,
            year=2026
        )

        # Expected Net Salary: (base_salary / 31) * 1 day worked = 6000 / 31 = ~193.55
        self.assertAlmostEqual(float(payroll.net_salary), 6000.0 / 31.0, places=2)
