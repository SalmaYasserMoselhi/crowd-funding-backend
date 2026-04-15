import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .models import OTP

def send_otp_email(user, purpose="activation"):
    otp_code = str(random.randint(100000, 999999))
    
    OTP.objects.update_or_create(
        user=user,
        purpose=purpose,
        defaults={'code': otp_code, 'created_at': timezone.now()}
    )

    context = {
        "user": user,
        "purpose": purpose,
        "otp_code": otp_code
    }

    html_content = render_to_string('authentication/otp_email.html', context)
    text_content = f"Hello {user.first_name},\n\nYour verification code is: {otp_code}\n\nFor {purpose}\n\nThis code will expire in 10 minutes."
    
    subject = "Your CrowdFund Egypt Verification Code"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email
    
    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)