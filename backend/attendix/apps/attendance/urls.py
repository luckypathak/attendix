from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShiftViewSet, AttendanceViewSet, OvertimeViewSet

router = DefaultRouter()
router.register('shifts', ShiftViewSet, basename='shift')
router.register('records', AttendanceViewSet, basename='attendance')
router.register('overtime', OvertimeViewSet, basename='overtime')

urlpatterns = [
    path('', include(router.urls)),
]
