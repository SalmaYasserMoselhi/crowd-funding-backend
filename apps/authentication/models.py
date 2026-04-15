import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from datetime import timedelta

from core.models import TrackableModel


class User(AbstractUser, TrackableModel):
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )

    email = models.EmailField(unique=True)
    username = models.CharField(("usernamse"), max_length=150, blank=True)

    phone_regex = RegexValidator(
        regex=r'^01[0-2,5]{1}[0-9]{8}$',
        message='Phone number must be a valid Egyptian number (e.g., 01012345678).',
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=15)
    profile_picture = models.URLField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=False)

    birthdate = models.DateField(null=True, blank=True)
    facebook_profile = models.URLField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'phone_number']

    def __str__(self):
        return self.email

class OTP(models.Model):
    PURPOSE_CHOICES = (
        ('activation', 'Activation'),
        ('reset', 'Password Reset')
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='otp_verfication')
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='activation')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        expiration_time = self.created_at + timedelta(minutes=10)
        return timezone.now() <= expiration_time