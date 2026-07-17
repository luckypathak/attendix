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

