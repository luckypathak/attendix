from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

class Command(BaseCommand):
    help = 'Seeds initial Celery periodic tasks for Attendix OS (Event-Driven Architecture)'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding initial periodic tasks...')

        # 1. Intervals
        every_5_minutes, _ = IntervalSchedule.objects.get_or_create(every=5, period=IntervalSchedule.MINUTES)

        # 2. Crontabs (Nightly)
        midnight_crontab, _ = CrontabSchedule.objects.get_or_create(minute='0', hour='0', day_of_week='*', day_of_month='*', month_of_year='*')
        # 1 AM crontab for Request Cleanup
        one_am_crontab, _ = CrontabSchedule.objects.get_or_create(minute='0', hour='1', day_of_week='*', day_of_month='*', month_of_year='*')
        # 2 AM crontab for Photo Cleanup
        two_am_crontab, _ = CrontabSchedule.objects.get_or_create(minute='0', hour='2', day_of_week='*', day_of_month='*', month_of_year='*')

        # 3. Tasks configuration (ONLY KEEPS EVENT-DRIVEN AND ESSENTIAL NIGHTLY TASKS)
        tasks = [
            {
                'name': 'Location Tracker',
                'task': 'attendix.apps.attendance.tasks.location_tracker_task',
                'interval': every_5_minutes
            },
            {
                'name': 'Auto Absent Marker',
                'task': 'attendix.apps.attendance.tasks.auto_absent_marker_task',
                'crontab': midnight_crontab
            },
            {
                'name': 'Cleanup Expired Requests',
                'task': 'attendix.apps.attendance.tasks.cleanup_expired_requests_task',
                'crontab': one_am_crontab
            },
            {
                'name': 'Cleanup Attendance Photos',
                'task': 'attendix.apps.attendance.tasks.cleanup_attendance_photos_task',
                'crontab': two_am_crontab
            }
        ]

        # 4. Clean up all other deprecated tasks
        active_task_names = [t['name'] for t in tasks]
        deprecated_tasks = PeriodicTask.objects.exclude(name__in=active_task_names)
        
        deleted_count, _ = deprecated_tasks.delete()
        if deleted_count:
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} deprecated polling tasks from DB."))

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

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {created_count} periodic tasks and ensured clean architecture!'))
