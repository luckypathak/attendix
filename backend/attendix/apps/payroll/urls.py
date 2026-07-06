from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdvanceSalaryViewSet, PayrollViewSet

router = DefaultRouter()
router.register('advances', AdvanceSalaryViewSet, basename='advancesalary')
router.register('records', PayrollViewSet, basename='payroll')

urlpatterns = [
    path('', include(router.urls)),
]
