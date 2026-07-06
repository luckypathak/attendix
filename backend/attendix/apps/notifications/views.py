from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Notification, SMSGatewayDevice, SMSQueue
from .serializers import NotificationSerializer, SMSGatewayDeviceSerializer, SMSQueueSerializer
from .services import NotificationService


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['notification_type', 'status']

    def get_queryset(self):
        # Employees only view their own notifications
        return self.queryset.filter(recipient=self.request.user)


class SMSGatewayViewSet(viewsets.ModelViewSet):
    queryset = SMSGatewayDevice.objects.all()
    serializer_class = SMSGatewayDeviceSerializer
    # Allow authentication via API key check or standard login for setup
    permission_classes = [permissions.AllowAny]

    def _verify_api_key(self, request):
        # Standard custom api key verification
        key = request.headers.get('X-Attendix-Gateway-Key')
        from django.conf import settings
        return key == getattr(settings, 'SMS_GATEWAY_API_KEY', 'attendix_gateway_secret_api_key_123')

    @action(detail=False, methods=['get'], url_path='poll')
    def poll(self, request):
        if not self._verify_api_key(request):
            return Response({"detail": "Invalid SMS Gateway API key."}, status=status.HTTP_403_FORBIDDEN)

        device_id = request.query_params.get('device_id')
        if not device_id:
            return Response({"detail": "device_id query param is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Update last ping
        device, _ = SMSGatewayDevice.objects.get_or_create(
            device_id=device_id,
            defaults={'device_name': f"Android Device {device_id[:6]}", 'api_key': 'default'}
        )
        device.save() # Triggers auto-now updated last_ping

        payloads = NotificationService.get_pending_sms_for_device(device_id)
        return Response(payloads)

    @action(detail=False, methods=['post'], url_path='status')
    def update_status(self, request):
        if not self._verify_api_key(request):
            return Response({"detail": "Invalid SMS Gateway API key."}, status=status.HTTP_403_FORBIDDEN)

        device_id = request.data.get('device_id')
        sms_id = request.data.get('sms_id')
        status_val = request.data.get('status') # 'SUCCESS' or 'FAILED'
        sim_used = request.data.get('sim_used', 1)
        error_msg = request.data.get('error_message', '')

        if not device_id or not sms_id or not status_val:
            return Response({"detail": "device_id, sms_id, and status are required."}, status=status.HTTP_400_BAD_REQUEST)

        updated = NotificationService.update_sms_status(device_id, int(sms_id), status_val, int(sim_used), error_msg)
        if updated:
            return Response({"status": "updated"})
        return Response({"detail": "Device or SMS not found."}, status=status.HTTP_404_NOT_FOUND)


class SMSQueueViewSet(viewsets.ModelViewSet):
    queryset = SMSQueue.objects.all()
    serializer_class = SMSQueueSerializer
    permission_classes = [permissions.IsAuthenticated]
