import requests
from django.core.files.base import ContentFile
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        
        if sociallogin.account.provider == 'google':
            picture_url = sociallogin.account.extra_data.get('picture')
            
            if picture_url:
                user.profile_picture = sociallogin.account.extra_data.get('picture')
                user.is_active = True
                user.save()
        return user