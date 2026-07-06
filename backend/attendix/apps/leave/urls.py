from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeaveRequestViewSet, LeaveBalanceViewSet, HolidayViewSet, LeaveCategoryViewSet

router = DefaultRouter()
router.register('categories', LeaveCategoryViewSet, basename='leavecategory')
router.register('requests', LeaveRequestViewSet, basename='leaverequest')
router.register('balances', LeaveBalanceViewSet, basename='leavebalance')
router.register('holidays', HolidayViewSet, basename='holiday')

urlpatterns = [
    path('', include(router.urls)),
]
