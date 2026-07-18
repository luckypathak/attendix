from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
import json

class Command(BaseCommand):
    help = 'Seeds initial Celery periodic tasks for Attendix OS'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding initial periodic tasks...')

        # 1. Intervals
        every_minute, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.MINUTES)
        every_5_minutes, _ = IntervalSchedule.objects.get_or_create(every=5, period=IntervalSchedule.MINUTES)
        every_10_minutes, _ = IntervalSchedule.objects.get_or_create(every=10, period=IntervalSchedule.MINUTES)
        every_15_minutes, _ = IntervalSchedule.objects.get_or_create(every=15, period=IntervalSchedule.MINUTES)
        every_30_minutes, _ = IntervalSchedule.objects.get_or_create(every=30, period=IntervalSchedule.MINUTES)
        every_hour, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.HOURS)

        # 2. Crontabs (Nightly & Daily)
        midnight_crontab, _ = CrontabSchedule.objects.get_or_create(minute='0', hour='0', day_of_week='*', day_of_month='*', month_of_year='*')

        # 3. Tasks configuration
        tasks = [
            {
                'name': '1. Auto Checkout Engine',
                'task': 'attendix.apps.attendance.tasks.check_active_overtimes_task',
                'interval': every_minute
            },
            {
                'name': '2. Location Tracker',
                'task': 'attendix.apps.attendance.tasks.location_tracker_task',
                'interval': every_5_minutes
            },
            {
                'name': '3. Attendance Status Recalculation',
                'task': 'attendix.apps.attendance.tasks.attendance_status_recalculation_task',
                'interval': every_15_minutes
            },
            {
                'name': '4. Auto Absent Marker',
                'task': 'attendix.apps.attendance.tasks.auto_absent_marker_task',
                'interval': every_30_minutes
            },
            {
                'name': '5. Pending OT Reminder',
                'task': 'attendix.apps.attendance.tasks.pending_ot_reminder_task',
                'interval': every_10_minutes
            },
            {
                'name': '6. Analytics Refresh',
                'task': 'attendix.apps.attendance.tasks.analytics_refresh_task',
                'interval': every_15_minutes
            },
            {
                'name': '7. Payroll Sync',
                'task': 'attendix.apps.attendance.tasks.payroll_sync_task',
                'crontab': midnight_crontab
            },
            {
                'name': '8. Cleanup Expired Requests',
                'task': 'attendix.apps.attendance.tasks.cleanup_expired_requests_task',
                'crontab': midnight_crontab
            },
            {
                'name': '9. Database Health Check',
                'task': 'attendix.apps.attendance.tasks.database_health_check_task',
                'interval': every_hour
            },
            {
                'name': '10. Missed Checkout Reconciliation',
                'task': 'attendix.apps.attendance.tasks.missed_checkout_reconciliation_task',
                'crontab': midnight_crontab
            }
        ]

        created_count = 0
        for task_conf in tasks:
            task_obj, created = PeriodicTask.objects.get_or_create(
                name=task_conf['name'],
                defaults={
                    'task': task_conf['task'],
                    'interval': task_conf.get('interval'),
                    'crontab': task_conf.get('crontab'),
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created task: {task_conf['name']}"))
            else:
                # Update task path/schedule if already exists
                task_obj.task = task_conf['task']
                task_obj.interval = task_conf.get('interval')
                task_obj.crontab = task_conf.get('crontab')
                task_obj.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {created_count} periodic tasks!'))
