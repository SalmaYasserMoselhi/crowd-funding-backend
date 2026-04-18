from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    GoogleLoginAPI, UserAPIView, RegisterAPIView, LoginAPIView, 
    VerifyOTPAPIView, ResendOTPAPIView, ForgetPasswordApiView, 
    ResetPasswordApiView, LogoutAPIView, ChangePasswordAPIView, MeAPIView
)

urlpatterns = [
    # ... your other urls
    path('accounts/', include('allauth.urls')),
    path('google/', GoogleLoginAPI.as_view(), name='google_login'),

    path('users/', UserAPIView.as_view(), name='user_api'),
    path('forgetpassword/', ForgetPasswordApiView.as_view(), name='forget_password'),
    path('resetpassword/', ResetPasswordApiView.as_view(), name='reset_password'),

    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change_password'),

    path('otp/verify/', VerifyOTPAPIView.as_view(), name='verify_otp'),
    path('otp/resend/', ResendOTPAPIView.as_view(), name='resend_otp'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('me/', MeAPIView.as_view(), name='my_profile')
]