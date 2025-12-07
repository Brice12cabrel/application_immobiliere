# auth_api/urls.py
from django.urls import path
from .views import (
    RegisterView, SendOTPView, VerifyOTPView,
    ForgotPasswordView, ResetPasswordView,
    BecomeBailleurView, ApproveBailleurView, BailleurStatusView,
    check_superadmin_exists, create_superadmin,  # ← BIEN ICI
    list_users, set_role, create_user, delete_user
)
from .utils import CustomTokenObtainPairView


urlpatterns = [
    path('auth/register/', RegisterView.as_view()),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/send-otp/', SendOTPView.as_view()),
    path('auth/verify-otp/', VerifyOTPView.as_view()),
    path('auth/forgot-password/', ForgotPasswordView.as_view()),
    path('auth/reset-password/', ResetPasswordView.as_view()),

    path('bailleur/apply/', BecomeBailleurView.as_view()),
    path('bailleur/status/', BailleurStatusView.as_view()),
    path('admin/bailleur/approve/<int:user_id>/', ApproveBailleurView.as_view()),

    # SUPER ADMIN
    path('check-superadmin/', check_superadmin_exists),
    path('create-superadmin/', create_superadmin),
    
       # SUPER ADMIN ENDPOINTS
    path('admin/users/', list_users, name='list_users'),
    path('admin/set-role/<int:user_id>/', set_role, name='set_role'),
    path('admin/create-user/', create_user, name='create_user'),
    path('admin/delete-user/<int:user_id>/', delete_user, name='delete_user'),
]