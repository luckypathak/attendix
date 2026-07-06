import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from attendix.apps.company.models import Company, Department, Designation
from attendix.apps.authentication.models import User
from attendix.apps.employee.models import EmployeeProfile
from attendix.apps.attendance.models import Shift, Attendance, Overtime
from attendix.apps.leave.models import LeaveRequest, LeaveBalance, Holiday

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds initial demo and mock data for Attendix Workforce OS.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        # 1. Create Company
        company, _ = Company.objects.get_or_create(
            domain='attendix.com',
            defaults={
                'name': 'Attendix Technologies',
                'logo_url': 'https://res.cloudinary.com/demo/image/upload/v1620000000/sample.jpg',
                'address': '123 Tech Avenue, Silicon Valley, CA',
                'grace_period_minutes': 15,
                'late_limit_for_half_day': 3,
                'auto_checkout_hours': 10.00
            }
        )

        # 2. Create Departments
        engineering, _ = Department.objects.get_or_create(company=company, name='Engineering', defaults={'description': 'Software development'})
        hr, _ = Department.objects.get_or_create(company=company, name='Human Resources', defaults={'description': 'HR and recruiters'})
        sales, _ = Department.objects.get_or_create(company=company, name='Sales & Marketing', defaults={'description': 'Client acquisitions'})

        # 3. Create Designations
        swe, _ = Designation.objects.get_or_create(company=company, name='Software Engineer', defaults={'description': 'Frontend/Backend engineers'})
        lead_eng, _ = Designation.objects.get_or_create(company=company, name='Lead Engineer', defaults={'description': 'Tech Leads'})
        hr_mgr, _ = Designation.objects.get_or_create(company=company, name='HR Manager', defaults={'description': 'HR Management'})

        # 4. Create Shift
        shift, _ = Shift.objects.get_or_create(
            company=company,
            name='General Shift (9 AM - 6 PM)',
            defaults={
                'start_time': datetime.time(9, 0, 0),
                'end_time': datetime.time(18, 0, 0),
                'grace_period_minutes': 15
            }
        )

        # 5. Create Users
        # Superadmin
        if not User.objects.filter(role=User.Roles.SUPER_ADMIN).exists():
            User.objects.create_superuser(
                username='superadmin',
                email='admin@attendix.com',
                password='AdminPassword123!',
                role=User.Roles.SUPER_ADMIN
            )
            self.stdout.write('- Created Super Admin: superadmin / AdminPassword123!')

        # Company Admin
        admin_user, created = User.objects.get_or_create(
            username='attendix_admin',
            defaults={
                'email': 'admin@attendix.tech',
                'role': User.Roles.COMPANY_ADMIN,
                'company': company,
                'phone': '+15550001'
            }
        )
        if created:
            admin_user.set_password('AdminPassword123!')
            admin_user.save()
            self.stdout.write('- Created Company Admin: attendix_admin / AdminPassword123!')

        # HR Manager (acts as Manager)
        hr_user, created = User.objects.get_or_create(
            username='sarah_hr',
            defaults={
                'email': 'sarah.hr@attendix.tech',
                'role': User.Roles.MANAGER,
                'company': company,
                'phone': '+15550002'
            }
        )
        if created:
            hr_user.set_password('AdminPassword123!')
            hr_user.save()
            
            # Profile
            EmployeeProfile.objects.create(
                user=hr_user,
                department=hr,
                designation=hr_mgr,
                base_salary=7500.00,
                hourly_rate=45.00,
                joining_date=datetime.date(2025, 1, 1),
                bank_account_no='DE12345678901234567800',
                bank_ifsc_code='GENES1234'
            )
            self.stdout.write('- Created HR Manager: sarah_hr / AdminPassword123!')

        # Employee (Developer)
        dev_user, created = User.objects.get_or_create(
            username='john_dev',
            defaults={
                'email': 'john.dev@attendix.tech',
                'role': User.Roles.EMPLOYEE,
                'company': company,
                'phone': '+15550003'
            }
        )
        if created:
            dev_user.set_password('AdminPassword123!')
            dev_user.save()
            
            # Profile
            EmployeeProfile.objects.create(
                user=dev_user,
                department=engineering,
                designation=swe,
                manager=hr_user,
                base_salary=6000.00,
                hourly_rate=35.00,
                joining_date=datetime.date(2025, 6, 1),
                bank_account_no='DE12345678901234567811',
                bank_ifsc_code='GENES1234'
            )
            self.stdout.write('- Created Employee: john_dev / AdminPassword123!')

        # 6. Create Default Categories
        for cat_name in ['Casual Leave', 'Sick Leave', 'Paid Leave', 'Privilege Leave']:
            from attendix.apps.leave.models import LeaveCategory
            LeaveCategory.objects.get_or_create(company=company, name=cat_name)

        # 7. Create Holidays
        Holiday.objects.get_or_create(company=company, date=datetime.date(2026, 1, 1), defaults={'name': 'New Year\'s Day', 'is_paid': True})
        Holiday.objects.get_or_create(company=company, date=datetime.date(2026, 12, 25), defaults={'name': 'Christmas Day', 'is_paid': True})

        # 8. Create historical check-in/out records for john_dev
        today = timezone.now().date()
        for i in range(1, 6):
            date = today - datetime.timedelta(days=i)
            # Avoid weekends
            if date.weekday() >= 5:
                continue
                
            check_in_time = datetime.time(9, 5, 0)
            check_out_time = datetime.time(18, 5, 0)
            
            # Mock check-in and out coordinates
            Attendance.objects.update_or_create(
                employee=dev_user,
                date=date,
                defaults={
                    'shift': shift,
                    'check_in_time': check_in_time,
                    'check_out_time': check_out_time,
                    'status': Attendance.Statuses.PRESENT,
                    'check_in_lat': 37.774900,
                    'check_in_lng': -122.419400,
                    'check_in_accuracy': 10.0,
                    'check_in_address': 'Market Street, San Francisco, CA',
                    'check_in_device_info': 'iOS 17, iPhone 15',
                    'check_out_lat': 37.774900,
                    'check_out_lng': -122.419400,
                    'check_out_accuracy': 12.0,
                    'check_out_address': 'Market Street, San Francisco, CA',
                    'check_out_device_info': 'iOS 17, iPhone 15'
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
