from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeaveRequestViewSet, LeaveBalanceViewSet, HolidayViewSet

router = DefaultRouter()
router.register('requests', LeaveRequestViewSet, basename='leaverequest')
router.register('balances', LeaveBalanceViewSet, basename='leavebalance')
router.register('holidays', HolidayViewSet, basename='holiday')

urlpatterns = [
    path('', include(router.urls)),
]
