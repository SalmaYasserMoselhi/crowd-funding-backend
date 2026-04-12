from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    ActivateAccountView,
    ChangePasswordView,
    DeleteAccountView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    UserProfileView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('activate/<uuid:token>/', ActivateAccountView.as_view(), name='auth-activate'),
    path('login/', TokenObtainPairView.as_view(), name='auth-login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='auth-login-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', UserProfileView.as_view(), name='auth-me'),
    path('me/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('me/delete/', DeleteAccountView.as_view(), name='auth-delete'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='auth-password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
]
