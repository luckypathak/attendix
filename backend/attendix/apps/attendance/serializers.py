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
            hrs = round(diff_secs / 3600.0, 2)
            hrs_str = f"{int(hrs)} Hours" if hrs.is_integer() else f"{hrs} Hours"
            ret['working_hours'] = hrs_str
        else:
            ret['working_hours'] = '--'
        return ret


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.username', read_only=True)
    shift_name = serializers.CharField(source='shift.name', read_only=True)
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

