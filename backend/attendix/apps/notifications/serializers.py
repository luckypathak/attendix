from rest_framework import serializers
from .models import Notification, SMSGatewayDevice, SMSQueue


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class SMSGatewayDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSGatewayDevice
        fields = '__all__'


class SMSQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSQueue
        fields = '__all__'
