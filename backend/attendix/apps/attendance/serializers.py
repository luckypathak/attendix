from rest_framework import serializers
from .models import Shift, Attendance, Overtime, AttendanceSession


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'
        read_only_fields = ('company',)


class AttendanceSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceSession
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.check_in_time:
            ret['check_in_time'] = instance.check_in_time.strftime('%I:%M %p')
        if instance.check_out_time:
            ret['check_out_time'] = instance.check_out_time.strftime('%I:%M %p')
        if instance.check_in_time and instance.check_out_time:
            import datetime
            dt_in = datetime.datetime.combine(datetime.date(2000, 1, 1), instance.check_in_time)
            dt_out = datetime.datetime.combine(datetime.date(2000, 1, 1), instance.check_out_time)
            if instance.check_out_time < instance.check_in_time:
                dt_out += datetime.timedelta(days=1)
            diff_secs = (dt_out - dt_in).total_seconds()
            hrs = int(diff_secs // 3600)
            mins = int((diff_secs % 3600) // 60)
            ret['working_hours'] = f"{hrs}h {mins}m"
        else:
            ret['working_hours'] = '--'
        return ret


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.username', read_only=True)
    shift_name = serializers.CharField(source='shift.name', read_only=True)
    shift_start_time = serializers.TimeField(source='shift.start_time', read_only=True)
    shift_end_time = serializers.TimeField(source='shift.end_time', read_only=True)
    sessions = AttendanceSessionSerializer(many=True, read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.check_in_time:
            ret['check_in_time'] = instance.check_in_time.strftime('%I:%M %p')
        if instance.check_out_time:
            ret['check_out_time'] = instance.check_out_time.strftime('%I:%M %p')
        # Always recompute from sessions on the fly to avoid database field caching/corruption
        computed_hrs = instance.computed_worked_hours
        if computed_hrs:
            dec_hrs = float(computed_hrs)
            ret['total_worked_hours'] = str(dec_hrs) # Override the DB field with computed truth
            
            hrs = int(dec_hrs)
            mins = int(round((dec_hrs - hrs) * 60))
            if mins == 60:
                hrs += 1
                mins = 0
            ret['formatted_worked_hours'] = f"{hrs}h {mins}m"
        else:
            ret['total_worked_hours'] = '0.00'
            ret['formatted_worked_hours'] = '0h 0m'

        # Add a flag to indicate if we are in the shift end window
        from django.utils import timezone
        import datetime
        ret['in_shift_window'] = False
        if instance.shift and instance.shift.end_time:
            now = timezone.now().time()
            # simple calculation, assuming no midnight crossing for shift_end for this check
            today = datetime.date.today()
            dt_now = datetime.datetime.combine(today, now)
            dt_end = datetime.datetime.combine(today, instance.shift.end_time)
            
            # window: 15 mins before to 15 mins after
            start_window = dt_end - datetime.timedelta(minutes=15)
            end_window = dt_end + datetime.timedelta(minutes=15)
            
            if start_window <= dt_now <= end_window:
                ret['in_shift_window'] = True
                
        return ret


class OvertimeSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)

    class Meta:
        model = Overtime
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.shift_start:
            ret['shift_start'] = instance.shift_start.strftime('%I:%M %p')
        if instance.shift_end:
            ret['shift_end'] = instance.shift_end.strftime('%I:%M %p')
        if instance.actual_current_time:
            ret['actual_current_time'] = instance.actual_current_time.strftime('%I:%M %p')
        from attendix.apps.attendance.services import AttendanceService
        shift = instance.attendance.shift or AttendanceService.get_active_shift(instance.employee)
        ret['shift_duration'] = f"{shift.duration_hours} hrs" if shift else "N/A"
        return ret


class CheckInSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    accuracy = serializers.FloatField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    device_info = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    captured_image = serializers.ImageField(required=True)


class CheckOutSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    accuracy = serializers.FloatField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    device_info = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    captured_image = serializers.ImageField(required=True)

