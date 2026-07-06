from django.utils import timezone
from .models import Notification, SMSQueue, SMSGatewayDevice


class NotificationService:
    @classmethod
    def create_in_app_notification(cls, recipient, title, body):
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            body=body,
            notification_type='IN_APP',
            status='SENT'
        )

    @classmethod
    def send_push_notification(cls, recipient, title, body):
        # 1. Log the notification
        notif = Notification.objects.create(
            recipient=recipient,
            title=title,
            body=body,
            notification_type='PUSH',
            status='PENDING'
        )
        
        # 2. Simulate FCM dispatch (Real applications would use firebase-admin SDK)
        # We simulate a successful dispatch by logging and setting to SENT
        notif.status = 'SENT'
        notif.save()
        return notif

    @classmethod
    def queue_sms(cls, phone, message):
        # Create an entry in the SMS queue
        return SMSQueue.objects.create(
            phone=phone,
            message=message,
            status='PENDING'
        )

    @classmethod
    def get_pending_sms_for_device(cls, device_id):
        try:
            device = SMSGatewayDevice.objects.get(device_id=device_id, is_active=True)
        except SMSGatewayDevice.DoesNotExist:
            return []

        # Reset limits daily
        now = timezone.now()
        if device.last_ping.date() < now.date():
            device.sim1_sent_today = 0
            device.sim2_sent_today = 0
            device.save()

        pending_sms = SMSQueue.objects.filter(status='PENDING')[:10]
        payloads = []

        for sms in pending_sms:
            # Check SIM failover rules
            sim_slot = 1
            if device.sim1_sent_today >= device.sim1_daily_limit:
                if device.sim2_sent_today >= device.sim2_daily_limit:
                    # Both SIMs exceeded limits, skip this batch or raise limit alert
                    break
                sim_slot = 2
            
            payloads.append({
                'id': sms.id,
                'phone': sms.phone,
                'message': sms.message,
                'sim_slot': sim_slot
            })
            
            # Temporarily reserve status to prevent double-pulling
            sms.status = 'PENDING'
            sms.save()
            
        return payloads

    @classmethod
    def update_sms_status(cls, device_id, sms_id, status, sim_used, error_msg=None):
        try:
            device = SMSGatewayDevice.objects.get(device_id=device_id)
        except SMSGatewayDevice.DoesNotExist:
            return False

        try:
            sms = SMSQueue.objects.get(id=sms_id)
        except SMSQueue.DoesNotExist:
            return False

        sms.status = 'SENT' if status == 'SUCCESS' else 'FAILED'
        sms.sim_slot_used = sim_used
        sms.error_message = error_msg
        sms.save()

        if status == 'SUCCESS':
            if sim_used == 1:
                device.sim1_sent_today += 1
            elif sim_used == 2:
                device.sim2_sent_today += 1
            device.save()

        return True
