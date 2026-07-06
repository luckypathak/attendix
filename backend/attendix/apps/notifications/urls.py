from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, SMSGatewayViewSet, SMSQueueViewSet

router = DefaultRouter()
router.register('feed', NotificationViewSet, basename='notification')
router.register('gateway', SMSGatewayViewSet, basename='smsgateway')
router.register('queue', SMSQueueViewSet, basename='smsqueue')

urlpatterns = [
    path('', include(router.urls)),
]
