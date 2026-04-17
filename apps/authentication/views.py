# views.py
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, OTP
from .utils import send_otp_email
from .serializer import UserSerializer, RegisterationSerializer
from datetime import datetime


class GoogleLoginAPI(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://127.0.0.1:8000/" # This should match the redirect URI in Google Console, even if not used by the API
    client_class = OAuth2Client


class UserAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, fromat=None):
        users = User.objects.filter(is_active = True)
        serializer = UserSerializer(users, many=True)
        return Response({"status":"successful", "length": len(users),"data": serializer.data}, status=200)

    def patch(self, request, format=None):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "successful", "data": serializer.data}, status=200)
        return Response({"status": "error", "error message": serializer.errors}, status=400)

    # def post(self, request, fromat=None):
    def delete(self, request, fromat=None):
        user = request.user
        user.is_active = False
        user.deleted_at = datetime.now()
        user.save()
        return Response({"status":"successful", "messgae":f"user {user.first_name} deleted successfully"}, status=204)


#there is a security issue that we save the user into the database even if he didn't activate it from the 
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, fromat=None):
        serializer = RegisterationSerializer(data=request.data)

        if (serializer.is_valid()):
            user = serializer.save()
            send_otp_email(user, purpose='activation')
            # refresh = RefreshToken.for_user(user)

            return Response({
                "status": "success",
                "message": "Account created successfully please check your email!",
                "User": {
                    "id": str(user.id),
                    "email": user.email
                }
            },
                status=201
            )
        return Response({"status":"error", "Error message":serializer.errors}, status=400)

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, fromat=None):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)

        if user:
            if not user.is_active:
                return Response({"status": "error", "Error message": "this account need to be activate"}, status=401)
            refresh = RefreshToken.for_user(user)

            return Response({
                "status": 'success',
                "Tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }
            }, status=200)
        else:
            return Response({"status": 'error', "Error messgae": "invalid password or email"}, status=401)


class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp')
        try:
            user = User.objects.get(email=email)
            otp_record = user.otp_verfication
            if otp_record.purpose != 'activation':
                return Response({"error": "This OTP is not for account activation."}, status=400)
            if otp_record.code != str(otp_code):
                return Response({"error": "Invalid OTP code."}, status=400)
            if not otp_record.is_valid():
                return Response({"error": "OTP has expired. Please request a new one."}, status=400)
            
            user.is_active = True
            refresh = RefreshToken.for_user(user)
            user.save()
            otp_record.delete()\n
            return Response({
                "message": "Email verified successfully!",
                "Tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }
            }, status=200)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=400)
        except OTP.DoesNotExist:
            return Response({"error": "No OTP found for this user."}, status=400)


class ResendOTPAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            email = request.data.get('email')
            user = User.objects.get(email=email)
            send_otp_email(user)
            return Response({"status": "success", "message": "please go check your email"}, status=200)
        except User.DoesNotExist():
            return Response({"status": "fail", "message": "user doesn't exist"}, status=400)


class ForgetPasswordApiView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            email = request.data.get('email')
            if not email:
                return Response({"status": "error", "message": "email is required."}, status=400)
            user = User.objects.get(email=email)
            send_otp_email(user, purpose="reset")    
            return Response({"status": "success", "message": "please check you email!"}, status=200)
        except User.DoesNotExist:
            return Response({"status": "error", "message": "User matching this email does not exist."}, status=400)

from rest_framework_simplejwt.tokens import TokenError

class ResetPasswordApiView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp')
        new_password = request.data.get('new_password')
        
        if not new_password:
             return Response({"error": "new_password is required."}, status=400)

        try:
            user = User.objects.get(email=email)
            otp_record = user.otp_verfication
            if otp_record.purpose != 'reset':
                return Response({"error": "This OTP is not for password reset."}, status=400)
            if otp_record.code != str(otp_code):
                return Response({"error": "Invalid OTP code."}, status=400)
            if not otp_record.is_valid():
                return Response({"error": "OTP has expired. Please request a new one."}, status=400)
            
            user.is_active = True
            user.set_password(new_password)
            user.save()

            otp_record.delete()
            
            return Response({"status": "success", "message": "Password reset successfully! You can now log in."}, status=200)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=400)
        except OTP.DoesNotExist:
            return Response({"error": "No OTP found for this user."}, status=400)


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"error": "Refresh token is required."}, status=400)
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"status": "success", "message": "Successfully logged out."}, status=200)
        except TokenError as e:
            return Response({"error": "Invalid token."}, status=400)


class ChangePasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        
        if not old_password or not new_password:
            return Response({"error": "old_password and new_password are required."}, status=400)
            
        if not user.check_password(old_password):
            return Response({"error": "Wrong old password."}, status=400)
            
        user.set_password(new_password)
        user.save()
        return Response({"status": "success", "message": "Password updated successfully."}, status=200)

class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response({"status": "success", "data": serializer.data}, status=200)
    
    def patch(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "successful", "data": serializer.data}, status=200)
        return Response({"status": "error", "error message": serializer.errors}, status=400)