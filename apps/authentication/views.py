from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ActivationToken
from .serializers import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        token = ActivationToken.objects.create(user=user)
        activation_url = f"{settings.FRONTEND_URL}/activate/{token.token}"
        body = render_to_string(
            'emails/activation.html',
            {'user': user, 'activation_url': activation_url},
        )
        send_mail(
            subject='Activate your CrowdFund Egypt account',
            message=activation_url,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=body,
        )


class ActivateAccountView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            activation = ActivationToken.objects.get(token=token)
        except ActivationToken.DoesNotExist:
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)

        if activation.is_expired():
            activation.delete()
            return Response({'detail': 'Token expired.'}, status=status.HTTP_400_BAD_REQUEST)

        user = activation.user
        user.is_active = True
        user.save(update_fields=['is_active'])
        activation.delete()
        return Response({'detail': 'Account activated.'}, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Password changed.'}, status=status.HTTP_200_OK)


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get('password', '')
        if not request.user.check_password(password):
            return Response({'detail': 'Incorrect password.'}, status=status.HTTP_400_BAD_REQUEST)
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'If this email exists, a reset link was sent.'})

        token, _ = ActivationToken.objects.get_or_create(user=user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token.token}"
        body = render_to_string(
            'emails/password_reset.html',
            {'user': user, 'reset_url': reset_url},
        )
        send_mail(
            subject='Reset your CrowdFund Egypt password',
            message=reset_url,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=body,
        )
        return Response({'detail': 'If this email exists, a reset link was sent.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            activation = ActivationToken.objects.get(token=serializer.validated_data['token'])
        except ActivationToken.DoesNotExist:
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)

        if activation.is_expired():
            activation.delete()
            return Response({'detail': 'Token expired.'}, status=status.HTTP_400_BAD_REQUEST)

        user = activation.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        activation.delete()
        return Response({'detail': 'Password reset successful.'})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)
