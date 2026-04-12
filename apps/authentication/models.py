import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from core.models import TrackableModel


class User(AbstractUser, TrackableModel):
    email = models.EmailField(unique=True)

    phone_regex = RegexValidator(
        regex=r'^01[0-2,5]{1}[0-9]{8}$',
        message='Phone number must be a valid Egyptian number (e.g., 01012345678).',
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=15)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_active = models.BooleanField(default=False)

    birthdate = models.DateField(null=True, blank=True)
    facebook_profile = models.URLField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'phone_number']

    def __str__(self):
        return self.email


class ActivationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='activation_token')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(hours=24)

    def __str__(self):
        return f'ActivationToken({self.user.email})'
