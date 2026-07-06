from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import MyTokenObtainPairView, UserRegisterView, MeView, RegisterCompanyView

urlpatterns = [
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegisterView.as_view(), name='register_user'),
    path('register-company/', RegisterCompanyView.as_view(), name='register_company'),
    path('me/', MeView.as_view(), name='current_user'),
]
